"""Pytest collection helpers for Phase 4 discovery rules."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
import re

_TOP_LEVEL_TEST_PATH_PARTS = 2
_MIN_CANONICAL_TEST_PATH_PARTS = 4

_EXERCISE_TEST_STEM_RE = re.compile(r"^test_ex\d{3}(?:_.*)?$")


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


def find_noncanonical_exercise_test_sources(paths: Iterable[Path]) -> list[Path]:
    """Return ``test_exNNN*.py`` paths that do not live in canonical exercise-local tests."""

    offenders = []
    for path in paths:
        if _exercise_key_for_path(path) is None:
            continue
        if _is_canonical_test_path(path):
            continue
        offenders.append(path)
    return sorted(offenders)


def _exercise_key_for_path(path: Path) -> str | None:
    if path.suffix != ".py":
        return None
    stem = path.stem
    if not _EXERCISE_TEST_STEM_RE.match(stem):
        return None
    return stem.removeprefix("test_")


def _is_top_level_test_path(path: Path) -> bool:
    return len(path.parts) == _TOP_LEVEL_TEST_PATH_PARTS and path.parts[0] == "tests"


def _is_canonical_test_path(path: Path) -> bool:
    """Return True only for canonical exercise-local tests.

    Canonical layout (per ACTION_PLAN design rules):
    exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py
    """
    # Must live under the exercises/ root.
    if path.parts[0] != "exercises":
        return False

    # Expected structure: exercises, construct, exercise_key, "tests", filename
    if len(path.parts) != 5:
        return False

    _, _construct, exercise_key_dir, tests_dir, _filename = path.parts

    # The immediate subdirectory must be "tests".
    if tests_dir != "tests":
        return False

    # Filename must be a valid test_ex* file, and its key must match the directory name.
    exercise_key = _exercise_key_for_path(path)
    if exercise_key is None:
        return False

    return exercise_key_dir == exercise_key
