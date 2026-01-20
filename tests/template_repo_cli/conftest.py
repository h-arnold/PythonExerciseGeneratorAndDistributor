"""Test fixtures for template repository CLI tests."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def sample_exercises(repo_root: Path) -> dict[str, dict[str, Path]]:
    """Sample exercise file mappings for testing."""
    return {
        "ex001_sanity": {
            "notebook": repo_root / "notebooks/ex001_sanity.ipynb",
            "test": repo_root / "tests/test_ex001_sanity.py",
        },
        "ex002_sequence_modify_basics": {
            "notebook": repo_root / "notebooks/ex002_sequence_modify_basics.ipynb",
            "test": repo_root / "tests/test_ex002_sequence_modify_basics.py",
        },
    }


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_gh_success() -> MagicMock:
    """Mock successful gh CLI execution."""
    mock = MagicMock()
    mock.return_value = MagicMock(returncode=0, stdout='{"name": "test-repo"}', stderr="")
    return mock


@pytest.fixture
def mock_gh_failure() -> MagicMock:
    """Mock failed gh CLI execution."""
    mock = MagicMock()
    mock.return_value = MagicMock(returncode=1, stdout="", stderr="Error occurred")
    return mock


@pytest.fixture
def mock_gh_auth_error() -> MagicMock:
    """Mock gh CLI authentication error."""
    mock = MagicMock()
    mock.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr="error: authentication required. Run 'gh auth login'",
    )
    return mock
