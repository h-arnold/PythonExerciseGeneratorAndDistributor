from __future__ import annotations

from pathlib import Path

import pytest

from exercise_runtime_support.pytest_collection_guard import (
    find_duplicate_exercise_test_sources,
    find_noncanonical_exercise_test_sources,
)

pytest_plugins = ("pytester",)


def test_find_duplicate_exercise_test_sources_flags_top_level_and_canonical_duplicates() -> None:
    duplicates = find_duplicate_exercise_test_sources(
        [
            Path("tests/test_ex004_sequence_debug_syntax.py"),
            Path(
                "exercises/sequence/ex004_sequence_debug_syntax/tests/"
                "test_ex004_sequence_debug_syntax.py"
            ),
        ]
    )

    assert duplicates == {
        "ex004_sequence_debug_syntax": [
            Path("tests/test_ex004_sequence_debug_syntax.py"),
            Path(
                "exercises/sequence/ex004_sequence_debug_syntax/tests/"
                "test_ex004_sequence_debug_syntax.py"
            ),
        ]
    }


def test_find_duplicate_exercise_test_sources_ignores_noncanonical_nested_tests() -> None:
    duplicates = find_duplicate_exercise_test_sources(
        [
            Path("tests/test_ex123_example.py"),
            Path("tests/ex123_example/test_ex123_example.py"),
        ]
    )

    assert duplicates == {}


def test_find_noncanonical_exercise_test_sources_flags_all_repo_side_exnnn_tests() -> None:
    offenders = find_noncanonical_exercise_test_sources(
        [
            Path("tests/test_ex003_sequence_modify_variables.py"),
            Path("tests/ex123_example/test_ex123_example.py"),
            Path(
                "exercises/sequence/ex004_sequence_debug_syntax/tests/"
                "test_ex004_sequence_debug_syntax.py"
            ),
            Path("tests/test_helpers.py"),
        ]
    )

    assert offenders == [
        Path("tests/ex123_example/test_ex123_example.py"),
        Path("tests/test_ex003_sequence_modify_variables.py"),
    ]


def test_find_noncanonical_exercise_test_sources_ignores_renamed_blocker_tests() -> None:
    offenders = find_noncanonical_exercise_test_sources(
        [
            Path("tests/test_sequence_ex007_construct_checks.py"),
            Path("tests/exercise_framework/test_canonical_ex002_integration.py"),
        ]
    )

    assert offenders == []


def test_find_noncanonical_exercise_test_sources_ignores_nonexercise_repo_tests() -> None:
    offenders = find_noncanonical_exercise_test_sources(
        [
            Path("tests/test_exercise_type_docs.py"),
        ]
    )

    assert offenders == []


def test_find_noncanonical_exercise_test_sources_ignores_canonical_exercise_local_tests() -> None:
    offenders = find_noncanonical_exercise_test_sources(
        [
            Path(
                "exercises/sequence/ex002_sequence_modify_basics/tests/"
                "test_ex002_sequence_modify_basics.py"
            ),
            Path(
                "exercises/sequence/ex004_sequence_debug_syntax/tests/"
                "test_ex004_sequence_debug_syntax.py"
            ),
            Path(
                "exercises/sequence/ex007_sequence_debug_casting/tests/"
                "test_ex007_sequence_debug_casting.py"
            ),
        ]
    )

    assert offenders == []


def test_pytest_collection_fails_with_usage_error_for_noncanonical_exercise_test_sources(
    pytester: pytest.Pytester,
) -> None:
    repo_conftest = Path(__file__).resolve().parents[1] / "conftest.py"
    pytester.makeconftest(
        f"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_CONFTEST_PATH = Path({str(repo_conftest)!r})
_spec = importlib.util.spec_from_file_location("repo_collection_conftest", _REPO_CONFTEST_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Could not load repository conftest from {{_REPO_CONFTEST_PATH}}")
_repo_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_repo_conftest)


pytest_collection_modifyitems = _repo_conftest.pytest_collection_modifyitems
"""
    )

    top_level_test = pytester.path / "tests" / "test_ex123_example.py"
    top_level_test.parent.mkdir(parents=True, exist_ok=True)
    top_level_test.write_text("def test_top_level():\n    assert True\n", encoding="utf-8")

    result = pytester.runpytest("--import-mode=importlib", "tests")

    result.stderr.fnmatch_lines(["*ERROR: Noncanonical exercise tests were collected*"])
    result.stderr.fnmatch_lines(["*tests/test_ex123_example.py*"])
    assert result.ret == pytest.ExitCode.USAGE_ERROR


def test_pytest_collection_fails_with_usage_error_for_duplicate_exercise_test_sources(
    pytester: pytest.Pytester,
) -> None:
    repo_conftest = Path(__file__).resolve().parents[1] / "conftest.py"
    pytester.makeconftest(
        f"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_CONFTEST_PATH = Path({str(repo_conftest)!r})
_spec = importlib.util.spec_from_file_location("repo_collection_conftest", _REPO_CONFTEST_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Could not load repository conftest from {{_REPO_CONFTEST_PATH}}")
_repo_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_repo_conftest)


pytest_collection_modifyitems = _repo_conftest.pytest_collection_modifyitems
"""
    )

    top_level_test = pytester.path / "tests" / "test_ex123_example.py"
    top_level_test.parent.mkdir(parents=True, exist_ok=True)
    top_level_test.write_text("def test_top_level():\n    assert True\n", encoding="utf-8")

    canonical_test = (
        pytester.path
        / "exercises"
        / "sequence"
        / "ex123_example"
        / "tests"
        / "test_ex123_example.py"
    )
    canonical_test.parent.mkdir(parents=True, exist_ok=True)
    canonical_test.write_text("def test_canonical():\n    assert True\n", encoding="utf-8")

    result = pytester.runpytest("--import-mode=importlib", "tests", "exercises")

    result.stderr.fnmatch_lines(["*ERROR: Duplicate exercise tests were collected*"])
    result.stderr.fnmatch_lines(["*ex123_example:*"])
    result.stderr.fnmatch_lines(["*tests/test_ex123_example.py*"])
    result.stderr.fnmatch_lines(["*exercises/sequence/ex123_example/tests/test_ex123_example.py*"])
    assert result.ret == pytest.ExitCode.USAGE_ERROR
