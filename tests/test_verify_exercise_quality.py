"""Tests for semantic modify-gate wiring checks in verify_exercise_quality."""

from __future__ import annotations

from pathlib import Path

from scripts.verify_exercise_quality import check_modify_gate_semantic_wiring


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_modify_gate_checks_skipped_for_non_modify_without_gate(tmp_path: Path) -> None:
    checker_path = tmp_path / "tests" / "student_checker" / "checks" / "ex222.py"
    _write(
        checker_path,
        """def run_ex222_checks() -> list[str]:\n    return []\n""",
    )

    findings = check_modify_gate_semantic_wiring(
        ex_slug="ex222_sequence_make_demo",
        repo_root=tmp_path,
        ex_type="make",
    )

    assert findings == []


def test_modify_gate_checks_error_when_required_assets_missing(tmp_path: Path) -> None:
    findings = check_modify_gate_semantic_wiring(
        ex_slug="ex111_sequence_modify_demo",
        repo_root=tmp_path,
        ex_type="modify",
    )

    messages = {finding.message for finding in findings}
    assert (
        "Missing student checker module: tests/student_checker/checks/ex111.py"
        in messages
    )
    assert (
        "Missing expectations module matching tests/exercise_expectations/ex111_*.py"
        in messages
    )
    assert (
        "Checker wiring must call check_modify_exercise_started with "
        "EX111_MODIFY_STARTER_BASELINES"
    ) in messages
    assert (
        "Missing modify-gate test module: tests/student_checker/test_modify_gate_ex111.py"
        in messages
    )


def test_modify_gate_checks_run_for_debug_when_checker_uses_gate(tmp_path: Path) -> None:
    checker_path = tmp_path / "tests" / "student_checker" / "checks" / "ex444.py"
    _write(
        checker_path,
        """

def run_ex444_checks() -> list[str]:
    gate_issues = check_modify_exercise_started("nb", 1, WRONG_BASELINES)
    return gate_issues
""",
    )
    expectation_module = (
        tmp_path / "tests" / "exercise_expectations" / "ex444_sequence_debug_demo.py"
    )
    _write(
        expectation_module,
        "EX444_MODIFY_STARTER_BASELINES = {'exercise1': 'print(1)'}\n",
    )

    findings = check_modify_gate_semantic_wiring(
        ex_slug="ex444_sequence_debug_demo",
        repo_root=tmp_path,
        ex_type="debug",
    )

    messages = {finding.message for finding in findings}
    assert (
        "Checker wiring must call check_modify_exercise_started with "
        "EX444_MODIFY_STARTER_BASELINES"
    ) in messages
    assert (
        "Missing modify-gate test module: tests/student_checker/test_modify_gate_ex444.py"
        in messages
    )


def test_modify_gate_checks_pass_when_semantically_wired(tmp_path: Path) -> None:
    checker_path = tmp_path / "tests" / "student_checker" / "checks" / "ex333.py"
    _write(
        checker_path,
        """
from tests.exercise_expectations import EX333_MODIFY_STARTER_BASELINES


def run_ex333_checks() -> list[str]:
    gate_issues = check_modify_exercise_started(
        "nb",
        1,
        EX333_MODIFY_STARTER_BASELINES,
    )
    return gate_issues
""",
    )
    expectation_module = (
        tmp_path / "tests" / "exercise_expectations" / "ex333_sequence_modify_demo.py"
    )
    _write(
        expectation_module,
        "EX333_MODIFY_STARTER_BASELINES = {'exercise1': 'print(1)'}\n",
    )
    modify_gate_test = (
        tmp_path / "tests" / "student_checker" / "test_modify_gate_ex333.py"
    )
    _write(modify_gate_test, "def test_placeholder() -> None:\n    assert True\n")

    findings = check_modify_gate_semantic_wiring(
        ex_slug="ex333_sequence_modify_demo",
        repo_root=tmp_path,
        ex_type="modify",
    )

    assert findings == []
