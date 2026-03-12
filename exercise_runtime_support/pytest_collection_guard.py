"""Pytest collection helpers for Phase 4 discovery rules."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

_TOP_LEVEL_TEST_PATH_PARTS = 2
_MIN_CANONICAL_TEST_PATH_PARTS = 4


def find_duplicate_exercise_test_sources(paths: Iterable[Path]) -> dict[str, list[Path]]:
    """Return duplicate exercise test sources collected from top-level and canonical paths."""

    top_level_by_key: dict[str, list[Path]] = defaultdict(list)
    canonical_by_key: dict[str, list[Path]] = defaultdict(list)

    for path in paths:
        exercise_key = _exercise_key_for_path(path)
        if exercise_key is None:
            continue
        if _is_top_level_test_path(path):
            top_level_by_key[exercise_key].append(path)
        elif _is_canonical_test_path(path):
            canonical_by_key[exercise_key].append(path)

    duplicates: dict[str, list[Path]] = {}
    for exercise_key, top_level_paths in top_level_by_key.items():
        canonical_paths = canonical_by_key.get(exercise_key)
        if canonical_paths:
            duplicates[exercise_key] = [*top_level_paths, *canonical_paths]
    return duplicates


def _exercise_key_for_path(path: Path) -> str | None:
    if path.suffix != ".py" or not path.name.startswith("test_ex"):
        return None
    return path.stem.removeprefix("test_")


def _is_top_level_test_path(path: Path) -> bool:
    return len(path.parts) == _TOP_LEVEL_TEST_PATH_PARTS and path.parts[0] == "tests"


def _is_canonical_test_path(path: Path) -> bool:
    if len(path.parts) < _MIN_CANONICAL_TEST_PATH_PARTS or path.parts[0] != "exercises":
        return False
    return "tests" in path.parts[1:-1]
