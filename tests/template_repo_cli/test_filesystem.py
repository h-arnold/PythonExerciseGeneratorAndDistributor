"""Tests for filesystem utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.template_repo_cli.utils.filesystem import (
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



