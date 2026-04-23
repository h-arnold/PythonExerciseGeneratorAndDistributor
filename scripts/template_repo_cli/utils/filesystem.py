"""Filesystem utilities."""

from __future__ import annotations

import shutil
from pathlib import Path


def safe_copy_file(source: Path, dest: Path) -> None:
    """Copy a file safely.

    Creates parent directories if needed.

    Args:
        source: Source file path.
        dest: Destination file path.

    Raises:
        FileNotFoundError: If source file doesn't exist.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    # Create parent directories if needed
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file
    shutil.copy2(source, dest)


def safe_copy_directory(
    source: Path,
    dest: Path,
    *,
    ignore_patterns: tuple[str, ...] | None = None,
) -> None:
    """Copy a directory recursively.

    Args:
        source: Source directory path.
        dest: Destination directory path.
        ignore_patterns: Optional glob patterns to exclude while copying.

    Raises:
        FileNotFoundError: If source directory doesn't exist.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")

    # Copy the entire directory tree
    ignore = None
    if ignore_patterns:
        ignore = shutil.ignore_patterns(*ignore_patterns)
    shutil.copytree(source, dest, dirs_exist_ok=True, ignore=ignore)



