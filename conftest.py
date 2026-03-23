"""Root conftest: enforce canonical exercise test location."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_EX_PATTERN = re.compile(r"test_ex\d{3}", re.IGNORECASE)
_CANONICAL_EXERCISES_ROOT = Path(__file__).parent / "exercises"
# Parts count for a canonical path inside exercises/: <construct>/<type>/<exercise_key>/tests/<file>
_CANONICAL_PARTS_COUNT = 5
_CANONICAL_TESTS_PART_INDEX = 3

# Exercises not yet migrated to canonical locations are exempt from the guard.
# Remove entries here once the exercise is moved into exercises/<construct>/<type>/<key>/tests/.
_NON_CANONICAL_EXEMPT = frozenset(
    [
        "test_ex001_sanity.py",  # ex001_sanity has no construct/type sub-tree yet
    ]
)


def pytest_collect_file(parent: pytest.Collector, file_path: Path) -> None:
    """Fail fast if a test_exNNN*.py file is outside the canonical exercises tree."""
    if not _EX_PATTERN.search(file_path.name):
        return None

    # Explicitly exempted non-canonical exercises (migration pending)
    if file_path.name in _NON_CANONICAL_EXEMPT:
        return None

    # Must be inside exercises/
    try:
        rel = file_path.relative_to(_CANONICAL_EXERCISES_ROOT)
    except ValueError:
        pytest.exit(
            f"BLOCKED: {file_path} matches test_exNNN pattern but is outside "
            f"exercises/. Move it to exercises/<construct>/<type>/<exercise_key>/tests/.",
            returncode=4,
        )

    # Must have exactly 5 parts: <construct>/<type>/<exercise_key>/tests/<file>
    # i.e., parts count inside exercises/ (0=construct, 1=type, 2=key, 3=tests, 4=file)
    parts = rel.parts
    if len(parts) != _CANONICAL_PARTS_COUNT or parts[_CANONICAL_TESTS_PART_INDEX] != "tests":
        pytest.exit(
            f"BLOCKED: {file_path} is inside exercises/ but not at the canonical path "
            f"exercises/<construct>/<type>/<exercise_key>/tests/<file>. Got: {rel}",
            returncode=4,
        )
