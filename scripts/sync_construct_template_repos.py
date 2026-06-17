"""Sync construct template repositories.

This script discovers construct directories under ``exercises/``, builds
workspace directories containing exercise files (notebooks, tests, metadata)
for each construct, and syncs them to GitHub template repositories.

Usage::

    # Dry-run (no GitHub operations)
    uv run python scripts/sync_construct_template_repos.py --dry-run --verbose

    # Publish all construct template repos
    uv run python scripts/sync_construct_template_repos.py

    # Publish with custom docs output path
    uv run python scripts/sync_construct_template_repos.py \\
        --docs-output-path docs/teachers/construct-template-repos.md
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Required, TypedDict

logger = logging.getLogger(__name__)


class SyncResult(TypedDict, total=False):
    """Result of syncing a single construct to a template repository."""

    success: Required[bool]
    construct: str
    repo_name: str
    dry_run: bool
    error: str
    message: str


def discover_constructs(repo_root: Path) -> list[str]:
    """Discover construct directories under the ``exercises/`` directory.

    Args:
        repo_root: Root directory of the repository.

    Returns:
        Sorted list of construct names (subdirectory names), excluding
        hidden directories and non-directory entries.
    """
    exercises_dir = repo_root / "exercises"
    if not exercises_dir.exists() or not exercises_dir.is_dir():
        return []

    constructs: list[str] = [
        entry.name
        for entry in sorted(exercises_dir.iterdir())
        if entry.is_dir() and not entry.name.startswith(".") and not entry.name.startswith("__")
    ]
    return constructs


def build_construct_workspace(repo_root: Path, construct: str, output_dir: Path) -> Path:
    """Build a workspace directory containing exercise files for a construct.

    Copies exercise files (student notebooks, exercise.json, and tests) from
    the construct's exercises into a workspace directory. Solution notebooks
    are excluded.

    Args:
        repo_root: Root directory of the repository.
        construct: Name of the construct (e.g., ``"sequence"``).
        output_dir: Directory where the workspace will be created.

    Returns:
        Path to the created workspace directory.

    Raises:
        FileNotFoundError: If the construct directory does not exist.
    """
    construct_dir = repo_root / "exercises" / construct
    if not construct_dir.exists() or not construct_dir.is_dir():
        raise FileNotFoundError(f"Construct directory not found: {construct_dir}")

    workspace = output_dir / construct
    workspace.mkdir(parents=True, exist_ok=True)

    # Copy construct-level additional-resources if present
    additional_resources = construct_dir / "additional-resources"
    if additional_resources.exists() and additional_resources.is_dir():
        shutil.copytree(
            additional_resources,
            workspace / "additional-resources",
            dirs_exist_ok=True,
            ignore=_ignore_pycache,
        )

    # Copy each exercise directory, excluding solution notebooks
    for exercise_dir in sorted(construct_dir.iterdir()):
        if not exercise_dir.is_dir() or exercise_dir.name.startswith("."):
            continue

        # Skip non-exercise directories
        if not (exercise_dir / "exercise.json").exists():
            continue

        # Build the destination path preserving the exercise structure
        dest_dir = workspace / exercise_dir.name
        dest_dir.mkdir(parents=True, exist_ok=True)

        _copy_exercise_files(exercise_dir, dest_dir)

    return workspace


def _ignore_pycache(dir: str, contents: list[str]) -> list[str]:
    return ["__pycache__"] if "__pycache__" in contents else []


def _copy_exercise_files(src: Path, dst: Path) -> None:
    """Copy exercise files from *src* to *dst*, excluding solution notebooks."""
    for item in src.iterdir():
        if item.name == "__pycache__":
            continue
        if item.name == "notebooks":
            _copy_notebooks(item, dst / "notebooks")
        elif item.is_dir():
            shutil.copytree(
                item,
                dst / item.name,
                dirs_exist_ok=True,
                ignore=_ignore_pycache,
            )
        elif item.is_file():
            shutil.copy2(item, dst / item.name)


def _copy_notebooks(src: Path, dst: Path) -> None:
    """Copy notebook files from *src* to *dst*, excluding solution notebooks."""
    dst.mkdir(parents=True, exist_ok=True)
    for nb_file in src.iterdir():
        if nb_file.name == "solution.ipynb":
            continue
        if nb_file.is_file():
            shutil.copy2(nb_file, dst / nb_file.name)


def _get_authenticated_owner(*, owner: str | None = None) -> str | None:
    """Return the GitHub owner for template repositories.

    If an explicit *owner* is provided, it takes precedence.
    Otherwise, the authenticated GitHub username is looked up
    via ``gh api user``.

    Args:
        owner: Explicit owner (GitHub username or organization name).

    Returns:
        Owner string if available, otherwise ``None``.
    """
    if owner:
        return owner
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            gh_owner = result.stdout.strip()
            return gh_owner if gh_owner else None
        return None
    except FileNotFoundError:
        return None


def _construct_repo_name(construct: str) -> str:
    return f"python-exercises-{construct}"


def sync_construct(  # noqa: PLR0913
    construct: str,
    workspace: Path,
    *,
    dry_run: bool = False,
    repo_root: Path | None = None,
    verbose: bool = False,
    github_owner: str | None = None,
) -> SyncResult:
    """Sync a construct to a GitHub template repository.

    Args:
        construct: Name of the construct (e.g., ``"sequence"``).
        workspace: Path to the workspace directory containing exercise files.
        dry_run: If True, simulate without making GitHub API calls.
        repo_root: Root of the repository (used for reference).
        verbose: If True, print progress information.
        github_owner: Explicit GitHub owner (user or org). Falls back to
            authenticated user if not provided.

    Returns:
        A ``SyncResult`` dictionary with success status and details.
    """
    repo_name = _construct_repo_name(construct)
    owner = _get_authenticated_owner(owner=github_owner)
    repo_ref = f"{owner}/{repo_name}" if owner else repo_name

    if verbose:
        src_info = f" from {repo_root}" if repo_root else ""
        logger.info(
            "Construct '%s': workspace=%s, target=%s%s",
            construct,
            workspace,
            repo_ref,
            src_info,
        )

    if dry_run:
        return SyncResult(
            success=True,
            construct=construct,
            repo_name=repo_name,
            dry_run=True,
            message=f"Dry-run: would create repository {repo_ref}",
        )

    # Check if the repo already exists
    repo_exists = False
    try:
        view_result: subprocess.CompletedProcess[str] = subprocess.run(
            ["gh", "repo", "view", repo_ref],
            capture_output=True,
            text=True,
            check=False,
        )
        repo_exists = view_result.returncode == 0
    except FileNotFoundError:
        return SyncResult(
            success=False,
            construct=construct,
            repo_name=repo_name,
            error="gh CLI not found. Is GitHub CLI installed?",
        )

    # Initialize git repo, commit, and push (force-push if repo exists)
    try:
        _init_and_push(workspace, repo_ref, verbose, repo_exists=repo_exists)
    except (subprocess.SubprocessError, OSError, RuntimeError) as e:
        return SyncResult(
            success=False,
            construct=construct,
            repo_name=repo_name,
            error=str(e),
        )

    # Mark as template (for new repos, also set template flag)
    if not repo_exists:
        subprocess.run(
            ["gh", "repo", "edit", repo_ref, "--template"],
            capture_output=True,
            text=True,
            check=False,
        )

    action = "Created" if not repo_exists else "Updated"
    return SyncResult(
        success=True,
        construct=construct,
        repo_name=repo_name,
        message=f"Successfully synced {repo_ref} ({action})",
    )


def _init_and_push(
    workspace: Path,
    repo_ref: str,
    verbose: bool = False,
    repo_exists: bool = False,
) -> None:
    """Initialize git repo, create/update on GitHub, and push.

    Assumes git is already installed and configured on the local machine.

    Args:
        workspace: Path to the workspace directory.
        repo_ref: GitHub repository reference (e.g., ``owner/name``).
        verbose: If True, print progress information.
        repo_exists: If True, force-push to the existing repository
            instead of creating a new one.

    Raises:
        RuntimeError: If git or gh operations fail.
    """
    # Initialize git
    subprocess.run(["git", "init"], cwd=workspace, capture_output=True, text=True, check=True)

    # Ensure default branch is 'main'
    subprocess.run(
        ["git", "checkout", "-b", "main"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )

    # Add all files and commit
    subprocess.run(["git", "add", "."], cwd=workspace, capture_output=True, text=True, check=True)
    commit_result = subprocess.run(
        ["git", "commit", "-m", "Sync template repository"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_result.returncode != 0 and "nothing to commit" not in commit_result.stderr:
        raise RuntimeError(f"Failed to commit files: {commit_result.stderr.strip()}")

    if repo_exists:
        # Force-push to existing repository
        subprocess.run(
            ["git", "remote", "add", "origin", f"https://github.com/{repo_ref}.git"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        push_result = subprocess.run(
            ["git", "push", "--force", "origin", "main"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        if push_result.returncode != 0:
            error_msg = push_result.stderr.strip() or "Unknown error"
            raise RuntimeError(f"Failed to push to existing repository {repo_ref}: {error_msg}")
    else:
        # Create repository on GitHub
        create_result = subprocess.run(
            ["gh", "repo", "create", repo_ref, "--public", "--source", ".", "--push"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )

        if create_result.returncode != 0:
            error_msg = create_result.stderr.strip() or "Unknown error"
            raise RuntimeError(f"Failed to create repository {repo_ref}: {error_msg}")

    if verbose:
        action = "Updated" if repo_exists else "Created and pushed"
        logger.info("%s repository: %s", action, repo_ref)


def generate_docs_page(
    constructs: list[str],
    repo_root: Path,
    *,
    github_owner: str | None = None,
) -> str:
    """Generate a markdown documentation page listing construct template repos.

    Args:
        constructs: List of construct names.
        repo_root: Root directory of the repository (used for exercise counting).
        github_owner: Explicit GitHub owner (user or org). Falls back to
            authenticated user if not provided.

    Returns:
        Markdown content as a string.
    """
    lines: list[str] = []
    lines.append("# Construct Template Repositories")
    lines.append("")
    lines.append(f"> Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(
        "This page lists the template repositories created for each construct. "
        "Each repository contains the exercises for that construct, ready to "
        "use in GitHub Classroom."
    )
    lines.append("")
    lines.append("## Available Constructs")
    lines.append("")
    lines.append("| Construct | Template Repository | Exercises |")
    lines.append("|-----------|-------------------|-----------|")

    owner = _get_authenticated_owner(owner=github_owner)

    for construct in reversed(constructs):
        repo_name = _construct_repo_name(construct)
        repo_ref = f"{owner}/{repo_name}" if owner else repo_name
        repo_url = f"https://github.com/{repo_ref}"

        # Count exercise directories for this construct
        construct_dir = repo_root / "exercises" / construct
        if construct_dir.exists():
            exercise_count = sum(
                1
                for entry in construct_dir.iterdir()
                if entry.is_dir()
                and not entry.name.startswith(".")
                and (entry / "exercise.json").exists()
            )
        else:
            exercise_count = 0

        lines.append(
            f"| [{construct.capitalize()}]({repo_url}) | `{repo_url}` | {exercise_count} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*This page is auto-generated. Do not edit manually.*")

    return "\n".join(lines) + "\n"


def write_docs_page(content: str, output_path: Path) -> None:
    """Write documentation content to a file, creating parent directories.

    Args:
        content: Markdown content to write (trailing newline added).
        output_path: Path to write the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure content ends with a single trailing newline
    text = content.rstrip("\n") + "\n"
    output_path.write_text(text)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed namespace with ``dry_run``, ``verbose``, and
        ``docs_output_path`` attributes.
    """
    parser = argparse.ArgumentParser(
        description="Sync construct template repositories to GitHub.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without making GitHub API calls.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information.",
    )
    parser.add_argument(
        "--docs-output-path",
        type=str,
        default="docs/teachers/construct-template-repos.md",
        help="Path to write the generated docs page.",
    )
    parser.add_argument(
        "--github-owner",
        type=str,
        default=None,
        help=(
            "GitHub owner (user or organization) for template repositories. "
            "Defaults to the authenticated GitHub user."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:  # noqa: C901
    """Main entry point for the sync script.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success, 1 if any construct failed.
    """
    args = parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    repo_root = Path(__file__).resolve().parent.parent
    constructs = discover_constructs(repo_root)

    if not constructs:
        logger.warning("No constructs discovered in %s", repo_root / "exercises")
        return 0

    if args.verbose:
        logger.info("Discovered constructs: %s", ", ".join(constructs))

    resolved_owner = _get_authenticated_owner(owner=args.github_owner)
    errors: list[str] = []

    for construct in constructs:
        _process_single_construct(
            construct,
            repo_root,
            args.dry_run,
            args.verbose,
            errors,
            github_owner=resolved_owner,
        )

    # Generate and write docs page
    docs_content = generate_docs_page(constructs, repo_root, github_owner=resolved_owner)
    docs_path = Path(args.docs_output_path)
    if not docs_path.is_absolute():
        docs_path = repo_root / docs_path
    write_docs_page(docs_content, docs_path)

    if args.verbose and docs_path.exists():
        logger.info("Docs page written to: %s", docs_path)

    if errors and args.verbose:
        logger.info("\nErrors encountered:")
        for error in errors:
            logger.info("  - %s", error)
    return 1 if errors else 0


def _process_single_construct(  # noqa: PLR0913
    construct: str,
    repo_root: Path,
    dry_run: bool,
    verbose: bool,
    errors: list[str],
    *,
    github_owner: str | None = None,
) -> None:
    """Sync a single construct and record any errors."""
    workspace: Path | None = None
    try:
        workspace = Path(tempfile.mkdtemp(prefix=f"{construct}_"))
        build_construct_workspace(repo_root, construct, workspace)

        result = sync_construct(
            construct,
            workspace,
            dry_run=dry_run,
            repo_root=repo_root,
            verbose=verbose,
            github_owner=github_owner,
        )

        if not result["success"]:
            error = result.get("error", "Unknown error")
            errors.append(f"{construct}: {error}")
            logger.error("Failed to sync construct '%s': %s", construct, error)
        elif verbose:
            logger.info(
                "Synced construct '%s': %s",
                construct,
                result.get("message", ""),
            )
    except Exception as e:  # noqa: BLE001
        errors.append(f"{construct}: {e}")
        logger.error("Error syncing construct '%s': %s", construct, e)
    finally:
        if workspace is not None:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
