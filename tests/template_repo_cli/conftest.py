"""Test fixtures for template repository CLI tests."""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Generator
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

import pytest

from scripts.template_repo_cli.core.collector import ExerciseFiles, FileCollector

if TYPE_CHECKING:
    from scripts.template_repo_cli.core.packager import TemplatePackager

ExerciseFileMap: TypeAlias = dict[str, ExerciseFiles]
ExerciseFileMapBuilder: TypeAlias = Callable[..., ExerciseFileMap]


@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def template_packager(
    repo_root: Path,
) -> TemplatePackager:
    """Provide a configured TemplatePackager for the repository."""

    from scripts.template_repo_cli.core.packager import TemplatePackager

    return TemplatePackager(repo_root)


@pytest.fixture
def build_exercise_file_map(repo_root: Path) -> ExerciseFileMapBuilder:
    """Build exercise file mappings for one or more exercise identifiers."""

    collector = FileCollector(repo_root)

    def _build(*exercise_ids: str) -> ExerciseFileMap:
        if not exercise_ids:
            msg = "At least one exercise_id is required"
            raise ValueError(msg)
        return collector.collect_multiple(list(exercise_ids))

    return _build
