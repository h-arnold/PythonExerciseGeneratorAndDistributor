"""Command-line interface for template repository creation."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from pathlib import Path

from scripts.template_repo_cli.core.collector import FileCollector
from scripts.template_repo_cli.core.github import GitHubClient
from scripts.template_repo_cli.core.packager import TemplatePackager
from scripts.template_repo_cli.core.selector import ExerciseSelector


def get_repo_root() -> Path:
    """Get repository root directory."""
    # Assume we're running from repository root
    return Path.cwd()


def _select_by_notebooks(args: argparse.Namespace, selector: ExerciseSelector) -> list[str]:
    """Select exercises by notebooks or patterns.
    
    Args:
        args: Parsed command-line arguments with notebooks list.
        selector: ExerciseSelector instance.
        
    Returns:
        List of exercise IDs.
    """
    exercises = []
    for pattern in args.notebooks:
        if "*" in pattern or "?" in pattern or "[" in pattern:
            exercises.extend(selector.select_by_pattern(pattern))
        else:
            exercises.extend(selector.select_by_notebooks([pattern]))
    return exercises


def _select_exercises(args: argparse.Namespace, selector: ExerciseSelector) -> list[str]:
    """Select exercises based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments.
        selector: ExerciseSelector instance.
        
    Returns:
        List of selected exercise IDs.
        
    Raises:
        ValueError: If selection criteria are invalid or no criteria provided.
    """
    if args.notebooks:
        return _select_by_notebooks(args, selector)
    elif args.construct and args.type:
        return selector.select_by_construct_and_type(args.construct, args.type)
    elif args.construct:
        return selector.select_by_construct(args.construct)
    elif args.type:
        return selector.select_by_type(args.type)
    else:
        raise ValueError("Must specify --construct, --type, or --notebooks")


def _check_github_prerequisites(github: GitHubClient) -> str | None:
    """Check GitHub CLI prerequisites.
    
    Args:
        github: GitHubClient instance.
        
    Returns:
        Error message if prerequisites not met, None otherwise.
    """
    if not github.check_gh_installed():
        return "gh CLI not installed. Please install it from https://cli.github.com/"
    
    if not github.check_authentication():
        return "Not authenticated with GitHub. Run 'gh auth login' first."
    
    return None


def _handle_output_directory(workspace: Path, output_dir: str, packager: TemplatePackager) -> int:
    """Handle copying workspace to output directory.
    
    Args:
        workspace: Workspace directory.
        output_dir: Output directory path.
        packager: TemplatePackager instance.
        
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    output_path = Path(output_dir)
    try:
        if output_path.exists():
            shutil.rmtree(output_path)
        shutil.copytree(workspace, output_path)
    except Exception as copy_error:
        traceback.print_exception(type(copy_error), copy_error, copy_error.__traceback__, file=sys.stderr)
        print(f"Error saving output to {output_path}: {copy_error}", file=sys.stderr)
        print(f"Workspace preserved at: {workspace}", file=sys.stderr)
        return 1
    
    packager.cleanup(workspace)
    print(f"Output saved to: {output_path}")
    return 0


def _build_template_package(
    workspace: Path,
    packager: TemplatePackager,
    files: dict,
    template_name: str,
    exercises: list[str],
    verbose: bool,
) -> bool:
    """Build the template package in workspace.
    
    Args:
        workspace: Workspace directory.
        packager: TemplatePackager instance.
        files: Collected exercise files.
        template_name: Name for the template.
        exercises: List of exercise IDs.
        verbose: Whether to print verbose output.
        
    Returns:
        True if successful, False otherwise.
    """
    packager.copy_exercise_files(workspace, files, include_solutions=True)
    packager.copy_template_base_files(workspace)
    packager.generate_readme(workspace, template_name, exercises)
    
    if not packager.validate_package(workspace):
        return False
    
    if verbose:
        print("Package validated successfully")
    
    return True


def _create_github_repo(
    args: argparse.Namespace,
    github: GitHubClient,
    workspace: Path,
) -> tuple[bool, str | None]:
    """Create GitHub repository if not in dry-run mode.
    
    Args:
        args: Parsed command-line arguments.
        github: GitHubClient instance.
        workspace: Workspace directory.
        
    Returns:
        Tuple of (success, error_message).
    """
    if args.dry_run:
        print(f"[DRY RUN] Would create repository: {args.repo_name}")
        print(f"[DRY RUN] Workspace: {workspace}")
        return True, None
    
    error_msg = _check_github_prerequisites(github)
    if error_msg:
        return False, error_msg
    
    result = github.create_repository(args.repo_name, workspace, push=False)
    
    if result["success"]:
        print(f"✓ Created repository: {args.repo_name}")
        return True, None
    else:
        return False, result.get("error", "Unknown error")


def _prepare_exercises(
    args: argparse.Namespace,
    selector: ExerciseSelector,
    collector: FileCollector,
) -> tuple[list[str], dict] | tuple[None, None]:
    """Prepare exercises: select and collect files.
    
    Args:
        args: Parsed command-line arguments.
        selector: ExerciseSelector instance.
        collector: FileCollector instance.
        
    Returns:
        Tuple of (exercises, files) on success, or (None, None) on error.
    """
    # Select exercises
    try:
        exercises = _select_exercises(args, selector)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return None, None
    
    if not exercises:
        print("No exercises found matching criteria", file=sys.stderr)
        return None, None
    
    if args.verbose:
        print(f"Selected {len(exercises)} exercises: {', '.join(exercises)}")
    
    # Collect files
    try:
        files = collector.collect_multiple(exercises)
    except FileNotFoundError as e:
        print(f"Error collecting files: {e}", file=sys.stderr)
        return None, None
    
    return exercises, files


def _handle_repository_creation(
    args: argparse.Namespace,
    github: GitHubClient,
    workspace: Path,
    packager: TemplatePackager,
    exercises: list[str],
) -> int:
    """Handle repository creation or dry-run output.
    
    Args:
        args: Parsed command-line arguments.
        github: GitHubClient instance.
        workspace: Workspace directory.
        packager: TemplatePackager instance.
        exercises: List of exercise IDs.
        
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if args.dry_run:
        print(f"[DRY RUN] Would create repository: {args.repo_name}")
        print(f"[DRY RUN] Workspace: {workspace}")
        print(f"[DRY RUN] Exercises: {', '.join(exercises)}")
        return 0
    
    success, error = _create_github_repo(args, github, workspace)
    if not success:
        print(f"Error creating repository: {error}", file=sys.stderr)
        packager.cleanup(workspace)
        return 1
    
    return 0


def _finalize_workspace(
    args: argparse.Namespace,
    workspace: Path,
    packager: TemplatePackager,
) -> int:
    """Finalize workspace - either cleanup or copy to output directory.
    
    Args:
        args: Parsed command-line arguments.
        workspace: Workspace directory.
        packager: TemplatePackager instance.
        
    Returns:
        Exit code (0 for success).
    """
    if not args.output_dir:
        packager.cleanup(workspace)
        return 0
    else:
        return _handle_output_directory(workspace, args.output_dir, packager)


def _execute_template_creation(
    args: argparse.Namespace,
    workspace: Path,
    packager: TemplatePackager,
    github: GitHubClient,
    files: dict,
    exercises: list[str],
) -> int:
    """Execute the template creation workflow.
    
    Args:
        args: Parsed command-line arguments.
        workspace: Workspace directory.
        packager: TemplatePackager instance.
        github: GitHubClient instance.
        files: Collected exercise files.
        exercises: List of exercise IDs.
        
    Returns:
        Exit code (0 for success).
    """
    try:
        # Build template package
        template_name = args.name or f"{args.repo_name} Exercises"
        if not _build_template_package(
            workspace, packager, files, template_name, exercises, args.verbose
        ):
            print("Error: Package validation failed", file=sys.stderr)
            packager.cleanup(workspace)
            return 1
        
        # Create GitHub repository
        result = _handle_repository_creation(args, github, workspace, packager, exercises)
        if result != 0:
            return result
        
        # Finalize workspace
        return _finalize_workspace(args, workspace, packager)
        
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        packager.cleanup(workspace)
        return 1
    # Defensive catch-all to ensure the CLI exits cleanly on truly unexpected
    # errors. Specific, anticipated exceptions are handled above; this block
    # is only for unexpected failures and still exposes a traceback in verbose
    # mode to aid debugging.
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        packager.cleanup(workspace)
        return 1


def create_command(args: argparse.Namespace) -> int:
    """Handle create command.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success).
    """
    repo_root = get_repo_root()
    
    if args.verbose:
        print(f"Repository root: {repo_root}")
    
    # Initialize components
    selector = ExerciseSelector(repo_root)
    collector = FileCollector(repo_root)
    packager = TemplatePackager(repo_root)
    github = GitHubClient(dry_run=args.dry_run)
    
    # Prepare exercises and files
    exercises, files = _prepare_exercises(args, selector, collector)
    if exercises is None:
        return 1
    
    # Create workspace
    workspace = packager.create_workspace()
    if args.verbose:
        print(f"Created workspace: {workspace}")
    
    # Execute template creation
    return _execute_template_creation(args, workspace, packager, github, files, exercises)


def list_command(args: argparse.Namespace) -> int:
    """Handle list command.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success).
    """
    repo_root = get_repo_root()
    selector = ExerciseSelector(repo_root)
    
    # Get exercises based on filters
    if args.construct:
        exercises = selector.select_by_construct([args.construct])
    else:
        # List all exercises
        exercises = selector.get_all_notebooks()
    
    # Print exercises
    if args.format == "json":
        print(json.dumps(exercises, indent=2))
    elif args.format == "table":
        print(f"{'Exercise ID':<40}")
        print("-" * 40)
        for ex in exercises:
            print(f"{ex:<40}")
    else:  # list format
        for ex in exercises:
            print(ex)
    
    return 0


def _select_exercises_for_validation(
    args: argparse.Namespace, selector: ExerciseSelector
) -> list[str]:
    """Select exercises for validation based on arguments.
    
    Args:
        args: Parsed command-line arguments.
        selector: ExerciseSelector instance.
        
    Returns:
        List of exercise IDs.
        
    Raises:
        ValueError: If invalid selection criteria or no criteria provided.
    """
    if args.construct and args.type:
        return selector.select_by_construct_and_type(args.construct, args.type)
    elif args.construct:
        return selector.select_by_construct(args.construct)
    elif args.type:
        return selector.select_by_type(args.type)
    else:
        raise ValueError("Must specify --construct or --type")


def validate_command(args: argparse.Namespace) -> int:
    """Handle validate command.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success).
    """
    repo_root = get_repo_root()
    selector = ExerciseSelector(repo_root)
    collector = FileCollector(repo_root)
    
    # Select exercises
    try:
        exercises = _select_exercises_for_validation(args, selector)
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1
    
    if not exercises:
        print("No exercises found matching criteria")
        return 0
    
    # Validate files exist
    print(f"Found {len(exercises)} exercises:")
    missing_files = []
    
    for ex in exercises:
        try:
            collector.collect_files(ex)
            print(f"  ✓ {ex}")
        except FileNotFoundError as e:
            print(f"  ✗ {ex}: {e}")
            missing_files.append(ex)
    
    if missing_files:
        print(f"\n{len(missing_files)} exercises have missing files")
        return 1
    
    print("\nAll exercises validated successfully")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
        
    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Create GitHub template repositories from exercise subsets"
    )
    
    # Global options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and validate without executing gh commands",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed progress"
    )
    parser.add_argument(
        "--output-dir", type=str, help="Local output directory (default: temp)"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create template repository")
    create_parser.add_argument(
        "--construct", nargs="+", help="One or more constructs"
    )
    create_parser.add_argument("--type", nargs="+", help="One or more exercise types")
    create_parser.add_argument(
        "--notebooks", nargs="+", help="Specific notebook patterns"
    )
    create_parser.add_argument(
        "--name", type=str, help="Template repository name/description"
    )
    create_parser.add_argument(
        "--repo-name", type=str, required=True, help="GitHub repository name (slug)"
    )
    create_parser.add_argument(
        "--private", action="store_true", help="Create as private repository"
    )
    create_parser.add_argument(
        "--org", type=str, help="Create in organization (default: user account)"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available exercises")
    list_parser.add_argument("--construct", type=str, help="Filter by construct")
    list_parser.add_argument("--type", type=str, help="Filter by type")
    list_parser.add_argument(
        "--format",
        choices=["table", "json", "list"],
        default="list",
        help="Output format",
    )
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate selection")
    validate_parser.add_argument("--construct", nargs="+", help="Filter by construct")
    validate_parser.add_argument("--type", nargs="+", help="Filter by type")
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # Execute command
    if args.command == "create":
        return create_command(args)
    elif args.command == "list":
        return list_command(args)
    elif args.command == "validate":
        return validate_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
