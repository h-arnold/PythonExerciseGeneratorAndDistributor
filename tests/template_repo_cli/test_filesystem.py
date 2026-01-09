"""Tests for filesystem utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template_repo_cli.utils.filesystem import (
    create_directory_structure,
    resolve_notebook_path,
    safe_copy_directory,
    safe_copy_file,
)


class TestSafeCopyFile:
    """Tests for safe file copying."""

    def test_copy_file_successfully(self, temp_dir: Path) -> None:
        """Test copying a file successfully."""
        source = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"
        source.write_text("test content")

        safe_copy_file(source, dest)

        assert dest.exists()
        assert dest.read_text() == "test content"

    def test_copy_file_creates_parent_directories(self, temp_dir: Path) -> None:
        """Test copying file creates parent directories."""
        source = temp_dir / "source.txt"
        dest = temp_dir / "subdir/nested/dest.txt"
        source.write_text("test content")

        safe_copy_file(source, dest)

        assert dest.exists()
        assert dest.read_text() == "test content"

    def test_copy_nonexistent_file_raises_error(self, temp_dir: Path) -> None:
        """Test copying nonexistent file raises FileNotFoundError."""
        source = temp_dir / "nonexistent.txt"
        dest = temp_dir / "dest.txt"

        with pytest.raises(FileNotFoundError):
            safe_copy_file(source, dest)

    def test_copy_file_overwrites_existing(self, temp_dir: Path) -> None:
        """Test copying file overwrites existing destination."""
        source = temp_dir / "source.txt"
        dest = temp_dir / "dest.txt"
        source.write_text("new content")
        dest.write_text("old content")

        safe_copy_file(source, dest)

        assert dest.read_text() == "new content"


class TestSafeCopyDirectory:
    """Tests for safe directory copying."""

    def test_copy_directory_successfully(self, temp_dir: Path) -> None:
        """Test copying a directory successfully."""
        source = temp_dir / "source_dir"
        dest = temp_dir / "dest_dir"
        source.mkdir()
        (source / "file1.txt").write_text("content1")
        (source / "file2.txt").write_text("content2")

        safe_copy_directory(source, dest)

        assert dest.exists()
        assert (dest / "file1.txt").read_text() == "content1"
        assert (dest / "file2.txt").read_text() == "content2"

    def test_copy_directory_with_subdirectories(self, temp_dir: Path) -> None:
        """Test copying directory with subdirectories."""
        source = temp_dir / "source_dir"
        dest = temp_dir / "dest_dir"
        source.mkdir()
        (source / "subdir").mkdir()
        (source / "file1.txt").write_text("content1")
        (source / "subdir/file2.txt").write_text("content2")

        safe_copy_directory(source, dest)

        assert (dest / "file1.txt").exists()
        assert (dest / "subdir/file2.txt").exists()
        assert (dest / "subdir/file2.txt").read_text() == "content2"

    def test_copy_nonexistent_directory_raises_error(self, temp_dir: Path) -> None:
        """Test copying nonexistent directory raises error."""
        source = temp_dir / "nonexistent_dir"
        dest = temp_dir / "dest_dir"

        with pytest.raises(FileNotFoundError):
            safe_copy_directory(source, dest)

    def test_copy_empty_directory(self, temp_dir: Path) -> None:
        """Test copying empty directory."""
        source = temp_dir / "empty_dir"
        dest = temp_dir / "dest_dir"
        source.mkdir()

        safe_copy_directory(source, dest)

        assert dest.exists()
        assert dest.is_dir()


class TestResolveNotebookPath:
    """Tests for notebook path resolution."""

    def test_resolve_notebook_path_absolute(self, repo_root: Path) -> None:
        """Test resolving absolute notebook path."""
        notebook_path = repo_root / "notebooks/ex001_sanity.ipynb"
        resolved = resolve_notebook_path(str(notebook_path))

        assert resolved == notebook_path
        assert resolved.is_absolute()

    def test_resolve_notebook_path_relative(self, repo_root: Path) -> None:
        """Test resolving relative notebook path."""
        resolved = resolve_notebook_path("notebooks/ex001_sanity.ipynb")

        assert resolved.is_absolute()
        assert resolved.name == "ex001_sanity.ipynb"

    def test_resolve_notebook_path_notebook_only(self, repo_root: Path) -> None:
        """Test resolving notebook path from name only."""
        resolved = resolve_notebook_path("ex001_sanity.ipynb")

        assert resolved.is_absolute()
        assert resolved.name == "ex001_sanity.ipynb"

    def test_resolve_notebook_path_nonexistent(self) -> None:
        """Test resolving nonexistent notebook path."""
        resolved = resolve_notebook_path("nonexistent.ipynb")

        # Should still resolve to a path, even if it doesn't exist
        assert resolved.is_absolute()
        assert resolved.name == "nonexistent.ipynb"


class TestCreateDirectoryStructure:
    """Tests for directory structure creation."""

    def test_create_single_directory(self, temp_dir: Path) -> None:
        """Test creating a single directory."""
        target = temp_dir / "new_dir"

        create_directory_structure(target)

        assert target.exists()
        assert target.is_dir()

    def test_create_nested_directories(self, temp_dir: Path) -> None:
        """Test creating nested directories."""
        target = temp_dir / "level1/level2/level3"

        create_directory_structure(target)

        assert target.exists()
        assert target.is_dir()

    def test_create_existing_directory(self, temp_dir: Path) -> None:
        """Test creating existing directory doesn't raise error."""
        target = temp_dir / "existing_dir"
        target.mkdir()

        # Should not raise error
        create_directory_structure(target)

        assert target.exists()

    def test_create_directory_with_parents(self, temp_dir: Path) -> None:
        """Test creating directory creates parent directories."""
        target = temp_dir / "parent/child"

        create_directory_structure(target)

        assert (temp_dir / "parent").exists()
        assert target.exists()
