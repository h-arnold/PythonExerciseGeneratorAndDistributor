"""Test fixtures for template repository CLI tests."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent.parent





@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)



