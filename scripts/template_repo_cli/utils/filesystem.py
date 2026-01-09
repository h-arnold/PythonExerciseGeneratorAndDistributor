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


def safe_copy_directory(source: Path, dest: Path) -> None:
    """Copy a directory recursively.
    
    Args:
        source: Source directory path.
        dest: Destination directory path.
        
    Raises:
        FileNotFoundError: If source directory doesn't exist.
    """
    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")
    
    # Copy the entire directory tree
    shutil.copytree(source, dest, dirs_exist_ok=True)


def resolve_notebook_path(notebook_path: str) -> Path:
    """Resolve notebook path.
    
    Converts relative or notebook-name-only paths to absolute paths.
    
    Args:
        notebook_path: Notebook path (absolute, relative, or just filename).
        
    Returns:
        Absolute Path object.
    """
    path = Path(notebook_path)
    
    # If already absolute, return it
    if path.is_absolute():
        return path
    
    # If it's just a filename (no directory parts), look in notebooks/
    if len(path.parts) == 1:
        # Assume it's in the notebooks directory
        return Path.cwd() / "notebooks" / path
    
    # Otherwise, resolve relative to current directory
    return Path.cwd() / path


def create_directory_structure(target: Path) -> None:
    """Create directory structure.
    
    Creates all parent directories as needed.
    
    Args:
        target: Target directory path to create.
    """
    target.mkdir(parents=True, exist_ok=True)
