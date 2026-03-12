from __future__ import annotations

from pathlib import Path

from exercise_runtime_support.pytest_collection_guard import (
    find_duplicate_exercise_test_sources,
)


def test_find_duplicate_exercise_test_sources_flags_top_level_and_canonical_duplicates() -> None:
    duplicates = find_duplicate_exercise_test_sources(
        [
            Path("tests/test_ex004_sequence_debug_syntax.py"),
            Path(
                "exercises/sequence/debug/ex004_sequence_debug_syntax/tests/"
                "test_ex004_sequence_debug_syntax.py"
            ),
        ]
    )

    assert duplicates == {
        "ex004_sequence_debug_syntax": [
            Path("tests/test_ex004_sequence_debug_syntax.py"),
            Path(
                "exercises/sequence/debug/ex004_sequence_debug_syntax/tests/"
                "test_ex004_sequence_debug_syntax.py"
            ),
        ]
    }


def test_find_duplicate_exercise_test_sources_ignores_noncanonical_nested_tests() -> None:
    duplicates = find_duplicate_exercise_test_sources(
        [
            Path("tests/test_ex002_sequence_modify_basics.py"),
            Path("tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py"),
        ]
    )

    assert duplicates == {}
