"""Sync construct template repositories.

This script discovers construct directories under ``exercises/`` and delegates
package construction and push to GitHub template repositories to ``repoman``
(via ``scripts/template_repo_cli``) using subprocess. The sync script is a thin
orchestrator: it does not copy exercise files itself, so ``repoman`` remains the
single source of truth for template-repo contents (including base files such as
``.devcontainer`` and the Classroom workflow).

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
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

_AUTH_ERROR_MARKERS = ("not authenticated", "gh auth", "401", "403", "unauthorized")


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


def _check_gh_auth() -> bool:
    """Return whether the GitHub CLI is authenticated.

    Runs ``gh auth status``. Returns ``False`` if ``gh`` is missing or not
    authenticated.

    Returns:
        ``True`` if authenticated, ``False`` otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def _looks_like_auth_error(text: str) -> bool:
    """Return whether *text* indicates a GitHub authentication problem."""
    lowered = text.lower()
    return any(marker in lowered for marker in _AUTH_ERROR_MARKERS)


def _log_repoman_output(combined: str, verbose: bool) -> None:
    """Emit repoman subprocess output at the appropriate log level."""
    if not combined:
        return
    if verbose:
        for line in combined.rstrip("\n").splitlines():
            logger.info("[repoman] %s", line)
    else:
        logger.error("[repoman] %s", combined.strip())


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


_AUTH_HINT = (
    "GitHub authentication failed. Run `gh auth login` and "
    "`gh auth refresh -s repo` to grant the required scopes, then retry."
)


class RepomanOptions(TypedDict):
    """Options forwarded to repoman subprocess invocations."""

    dry_run: bool
    verbose: bool
    org: str | None


def _run_repoman_command(
    subcommand: str,
    construct: str,
    repo_root: Path,
    options: RepomanOptions,
) -> subprocess.CompletedProcess[str]:
    """Run a repoman subcommand as a subprocess with *repo_root* as cwd.

    repoman expects its global ``--dry-run``/``--verbose`` flags before the
    subcommand, so they are inserted ahead of *subcommand*.
    """
    repo_name = _construct_repo_name(construct)
    cmd = [sys.executable, "-m", "scripts.template_repo_cli"]
    if options["dry_run"]:
        cmd.append("--dry-run")
    if options["verbose"]:
        cmd.append("--verbose")
    cmd.extend([subcommand, "--repo-name", repo_name, "--construct", construct])
    if options["org"]:
        cmd.extend(["--org", options["org"]])
    return subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)


def _report_repoman_failure(
    subcommand: str, construct: str, combined: str
) -> tuple[bool, str | None]:
    """Build a ``(success, error)`` result for a failed repoman command."""
    if _looks_like_auth_error(combined):
        return (
            False,
            f"repoman {subcommand} failed for '{construct}':\n{combined.strip()}\n\n{_AUTH_HINT}",
        )
    return False, f"repoman {subcommand} failed for '{construct}':\n{combined.strip()}"


def _create_fallback(
    construct: str,
    repo_root: Path,
    options: RepomanOptions,
) -> tuple[bool, str | None]:
    """Fall back to ``repoman create`` after a missing-repo update failure."""
    if options["verbose"]:
        repo_name = _construct_repo_name(construct)
        logger.info("Repository '%s' does not exist; creating via repoman", repo_name)

    if options["dry_run"]:
        # update --dry-run never contacts GitHub, so a missing repo is not real.
        return True, None

    create_result = _run_repoman_command("create", construct, repo_root, options)
    create_combined = (create_result.stdout or "") + (create_result.stderr or "")
    _log_repoman_output(create_combined, options["verbose"])

    if create_result.returncode == 0:
        return True, None

    return _report_repoman_failure("create", construct, create_combined)


def _sync_via_repoman(
    construct: str,
    repo_root: Path,
    *,
    dry_run: bool = False,
    verbose: bool = False,
    org: str | None = None,
) -> tuple[bool, str | None]:
    """Sync a construct's template repository by delegating to repoman.

    Runs ``repoman update`` (and, if the repo is missing, falls back to
    ``repoman create``) via subprocess. This keeps the sync script decoupled
    from repoman's internal package/push logic.

    Args:
        construct: Construct name (e.g. ``"sequence"``).
        repo_root: Repository root, used as the working directory for the
            child process (repoman resolves its root via ``Path.cwd()``).
        dry_run: If True, only attempt ``repoman update --dry-run``.
        verbose: If True, print repoman output and progress.
        org: Optional GitHub organization to host the template repos.

    Returns:
        Tuple of ``(success, error_message)`` where ``error_message`` is
        ``None`` on success.
    """
    options: RepomanOptions = {"dry_run": dry_run, "verbose": verbose, "org": org}

    if verbose:
        repo_name = _construct_repo_name(construct)
        logger.info("Syncing construct '%s' via repoman (repo=%s)", construct, repo_name)

    update_result = _run_repoman_command("update", construct, repo_root, options)
    combined = (update_result.stdout or "") + (update_result.stderr or "")

    if update_result.returncode == 0:
        if verbose:
            logger.info("repoman update succeeded for '%s'", construct)
        return True, None

    _log_repoman_output(combined, verbose)

    if _looks_like_auth_error(combined):
        return _report_repoman_failure("update", construct, combined)

    if "Run the create command first" not in combined:
        # Some other failure (validation, network, etc.) - do not fall back.
        return False, f"repoman update failed for '{construct}':\n{combined.strip()}"

    return _create_fallback(construct, repo_root, options)


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
            f"| [{construct.capitalize()}]({repo_url}) | `{repo_ref}` | {exercise_count} |"
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
        Parsed namespace with ``dry_run``, ``verbose``, ``docs_output_path``,
        ``github_owner``, and ``org`` attributes.
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
            "GitHub owner (user or organization) used in docs links. "
            "Defaults to the authenticated GitHub user."
        ),
    )
    parser.add_argument(
        "--org",
        type=str,
        default=None,
        help=(
            "GitHub organization to host the construct template repositories. "
            "Forwarded to repoman; defaults to the authenticated user account."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:  # noqa: C901
    """Main entry point for the sync script.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success, 1 if any construct failed or auth is missing.
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

    # Auth pre-check (skipped in dry-run, which never contacts GitHub).
    if not args.dry_run and not _check_gh_auth():
        logger.error(
            "Not authenticated with GitHub. Run `gh auth login` (and "
            "`gh auth refresh -s repo` for the required scopes) first."
        )
        return 1

    errors: list[str] = []

    for construct in constructs:
        _process_single_construct(
            construct,
            repo_root,
            args.dry_run,
            args.verbose,
            errors,
            org=args.org,
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
    org: str | None = None,
) -> None:
    """Sync a single construct via repoman and record any errors."""
    try:
        success, error = _sync_via_repoman(
            construct,
            repo_root,
            dry_run=dry_run,
            verbose=verbose,
            org=org,
        )
        if not success:
            errors.append(f"{construct}: {error}")
            logger.error("Failed to sync construct '%s': %s", construct, error)
        elif verbose:
            logger.info("Synced construct '%s'", construct)
    except Exception as e:  # noqa: BLE001
        errors.append(f"{construct}: {e}")
        logger.error("Error syncing construct '%s': %s", construct, e)


if __name__ == "__main__":
    raise SystemExit(main())
