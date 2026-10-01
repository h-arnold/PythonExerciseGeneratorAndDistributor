from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from scripts import verify_exercise_quality
from tests.exercise_metadata_helpers import make_exercise_json

# pyright: reportPrivateUsage=false


def _write_notebook(
    path: Path,
    *,
    include_explanation: bool = True,
    variant: str | None = "student",
    source: str = "print('Hello')\n",
) -> None:
    cells: list[dict[str, object]] = []
    if include_explanation:
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {
                    "language": "markdown",
                    "tags": ["explanation1"],
                },
                "source": ["What actually happened?\n"],
            }
        )

    cells.append(
        {
            "cell_type": "code",
            "metadata": {
                "language": "python",
                "tags": ["exercise1"],
            },
            "source": [source],
        },
    )

    # Add self-checker cell with variant override
    if variant:
        cells.append(
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "import os\n",
                    f'os.environ["PYTUTOR_ACTIVE_VARIANT"] = "{variant}"\n',
                    "from exercise_runtime_support.student_checker import run_notebook_checks\n",
                    "run_notebook_checks('placeholder')\n",
                ],
            }
        )

    notebook = {"cells": cells}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook), encoding="utf-8")


def _write_notebook_cells(path: Path, cells: list[dict[str, Any]]) -> None:
    notebook = {"cells": cells}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook), encoding="utf-8")


def _exercise_metadata(
    slug: str,
    *,
    exercise_type: str = "debug",
) -> dict[str, int | str]:
    return {
        "schema_version": 1,
        "exercise_key": slug,
        "exercise_id": 4,
        "slug": slug,
        "title": "Example Exercise",
        "construct": "sequence",
        "exercise_type": exercise_type,
        "parts": 1,
    }


def _write_order_of_teaching(repo_root: Path, slug: str) -> None:
    order_path = repo_root / "exercises" / "sequence" / "OrderOfTeaching.md"
    order_path.parent.mkdir(parents=True, exist_ok=True)
    order_path.write_text(f"{slug}\n", encoding="utf-8")


def _write_canonical_exercise(  # noqa: PLR0913
    repo_root: Path,
    slug: str,
    *,
    include_metadata: bool = True,
    metadata: dict[str, int | str] | None = None,
    include_explanation: bool = True,
    missing_paths: set[str] | None = None,
) -> Path:
    exercise_dir = repo_root / "exercises" / "sequence" / slug
    exercise_dir.mkdir(parents=True, exist_ok=True)
    missing_paths = missing_paths or set()

    if "README.md" not in missing_paths:
        (exercise_dir / "README.md").write_text("# README\n", encoding="utf-8")
    if include_metadata and "exercise.json" not in missing_paths:
        make_exercise_json(exercise_dir, metadata or _exercise_metadata(slug))
    if "notebooks/student.ipynb" not in missing_paths:
        _write_notebook(
            exercise_dir / "notebooks" / "student.ipynb",
            include_explanation=include_explanation,
            variant="student",
        )
    if "notebooks/solution.ipynb" not in missing_paths:
        _write_notebook(
            exercise_dir / "notebooks" / "solution.ipynb",
            include_explanation=include_explanation,
            variant="solution",
        )
    if "tests/test_file" not in missing_paths:
        test_path = exercise_dir / "tests" / f"test_{slug}.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("def test_placeholder() -> None:\n    assert True\n", encoding="utf-8")

    # Create supporting files to avoid Gate F/G failures
    if "tests/student_checker_support.py" not in missing_paths:
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "from __future__ import annotations\n"
            "from typing import Any\n"
            "CHECKS: list[Any] = [{'fake': 'check'}]\n",
            encoding="utf-8",
        )
    if "tests/expectations.py" not in missing_paths:
        expectations_path = exercise_dir / "tests" / "expectations.py"
        expectations_path.parent.mkdir(parents=True, exist_ok=True)
        expectations_path.write_text(
            "from __future__ import annotations\n"
            "from typing import Final\n"
            "EX004_EXPECTED_OUTPUTS: Final[dict[int, str]] = {1: ''}\n",
            encoding="utf-8",
        )

    _write_order_of_teaching(repo_root, slug)
    return exercise_dir


def _write_legacy_exercise_directory(repo_root: Path, slug: str) -> None:
    legacy_dir = repo_root / "exercises" / "sequence" / "debug" / slug
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "README.md").write_text("# Legacy README\n", encoding="utf-8")


def test_main_validates_canonical_exercise_layout_successfully(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    _write_canonical_exercise(tmp_path, slug)

    exit_code = verify_exercise_quality.main(
        [
            slug,
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Missing canonical file" not in captured.out
    assert "Could not resolve canonical exercise directory" not in captured.out
    assert "OK:" in captured.out


@pytest.mark.parametrize(
    ("missing_path", "expected_message"),
    [
        ("notebooks/solution.ipynb", "Missing canonical file: notebooks/solution.ipynb"),
        (
            "tests/test_file",
            "Missing canonical file: tests/test_ex004_sequence_debug_syntax.py",
        ),
    ],
)
def test_main_fails_when_required_canonical_files_are_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    missing_path: str,
    expected_message: str,
) -> None:
    slug = "ex004_sequence_debug_syntax"
    _write_canonical_exercise(
        tmp_path,
        slug,
        missing_paths={missing_path},
    )

    exit_code = verify_exercise_quality.main(
        [
            slug,
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected_message in captured.out
    # New gates may add additional warnings, so check for FAIL with at least 1 error
    assert "FAIL:" in captured.out
    assert "1 error(s)" in captured.out


@pytest.mark.parametrize(
    ("metadata", "expected_message"),
    [
        (None, "exercise.json not found"),
        (
            {
                **_exercise_metadata("ex004_sequence_debug_syntax"),
                "exercise_type": "invalid_type",
            },
            "Canonical exercise metadata must define a valid exercise_type",
        ),
    ],
)
def test_main_uses_canonical_metadata_without_legacy_fallback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    metadata: dict[str, int | str] | None,
    expected_message: str,
) -> None:
    slug = "ex004_sequence_debug_syntax"
    _write_canonical_exercise(
        tmp_path,
        slug,
        include_metadata=metadata is not None,
        metadata=metadata,
        include_explanation=False,
    )
    _write_legacy_exercise_directory(tmp_path, slug)

    exit_code = verify_exercise_quality.main(
        [
            slug,
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected_message in captured.out
    assert "Debug exercise expected explanationN tag(s) but none were found" not in captured.out
    assert captured.out.strip().endswith("FAIL: 1 error(s), 0 warning(s)")


def test_main_rejects_notebook_path_cli_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    exercise_dir = _write_canonical_exercise(tmp_path, slug)

    exit_code = verify_exercise_quality.main(
        [
            str(exercise_dir / "notebooks" / "student.ipynb"),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "resolver input must be an exercise_key, not a path-like string" in captured.out
    assert "Notebook not found" not in captured.out
    assert captured.out.strip().endswith("FAIL: 1 error(s), 0 warning(s)")


def test_main_fails_when_debug_explanation_tags_do_not_match_exercise_tags(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    exercise_dir = _write_canonical_exercise(tmp_path, slug)
    mismatched_cells = [
        {
            "cell_type": "markdown",
            "metadata": {"language": "markdown", "tags": ["explanation2"]},
            "source": ["What actually happened?\n"],
        },
        {
            "cell_type": "code",
            "metadata": {"language": "python", "tags": ["exercise1"]},
            "source": ["print('Hello')\n"],
        },
    ]
    _write_notebook_cells(exercise_dir / "notebooks" / "student.ipynb", mismatched_cells)
    _write_notebook_cells(exercise_dir / "notebooks" / "solution.ipynb", mismatched_cells)

    exit_code = verify_exercise_quality.main([slug, "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Debug exercise explanationN tags must exactly match exerciseN tags" in captured.out


def test_main_fails_when_student_solution_exercise_tags_do_not_match(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    exercise_dir = _write_canonical_exercise(tmp_path, slug)

    solution_cells = [
        {
            "cell_type": "markdown",
            "metadata": {"language": "markdown", "tags": ["explanation1"]},
            "source": ["What actually happened?\n"],
        },
        {
            "cell_type": "code",
            "metadata": {"language": "python", "tags": ["exercise1"]},
            "source": ["print('Hello')\n"],
        },
        {
            "cell_type": "markdown",
            "metadata": {"language": "markdown", "tags": ["explanation2"]},
            "source": ["What actually happened?\n"],
        },
        {
            "cell_type": "code",
            "metadata": {"language": "python", "tags": ["exercise2"]},
            "source": ["print('Hello again')\n"],
        },
    ]
    _write_notebook_cells(exercise_dir / "notebooks" / "solution.ipynb", solution_cells)

    exit_code = verify_exercise_quality.main([slug, "--repo-root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Student and solution notebooks must use the same exerciseN tags" in captured.out
    assert "Student and solution notebooks must use the same explanationN tags" in captured.out


# ═══════════════════════════════════════════════════════════════════════════════
# Gate F — Student checker support module
# ═══════════════════════════════════════════════════════════════════════════════


def _make_checker_test_exercise_dir(tmp_path: Path, slug: str) -> Path:
    """Create an exercise directory without student_checker_support.py
    or expectations.py for checker-module tests."""
    metadata: dict[str, int | str] = {
        **_exercise_metadata(slug),  # type: ignore[arg-type]
        "exercise_type": "modify",
        "parts": 1,
    }
    return _write_canonical_exercise(
        tmp_path,
        slug,
        metadata=metadata,
        include_explanation=False,
        missing_paths={"tests/student_checker_support.py", "tests/expectations.py"},
    )


class TestGateFStudentCheckerSupport:
    """Gate F: Verify student_checker_support.py exists with non-empty CHECKS."""

    def _make_exercise_dir(self, tmp_path: Path, slug: str) -> Path:
        return _make_checker_test_exercise_dir(tmp_path, slug)

    def test_missing_checker_support_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        findings = verify_exercise_quality._check_student_checker_support(exercise_dir)
        assert len(findings) > 0
        assert any(
            "student_checker_support" in f.message and f.severity == "ERROR" for f in findings
        )

    def test_empty_checks_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "from __future__ import annotations\nfrom typing import Any\nCHECKS: list[Any] = []\n",
            encoding="utf-8",
        )

        findings = verify_exercise_quality._check_student_checker_support(exercise_dir)
        assert len(findings) > 0
        assert any("CHECKS" in f.message and f.severity == "ERROR" for f in findings)

    def test_non_empty_checks_returns_no_finding(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "CHECKS = [{'tag': 'exercise1', 'check': None}]\n",
            encoding="utf-8",
        )

        findings = verify_exercise_quality._check_student_checker_support(exercise_dir)
        assert len(findings) == 0

    def test_unimportable_checker_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text("this is synta error!!!\n", encoding="utf-8")

        findings = verify_exercise_quality._check_student_checker_support(exercise_dir)
        assert len(findings) > 0
        assert any(f.severity == "ERROR" for f in findings)


# ═══════════════════════════════════════════════════════════════════════════════
# Gate G — Expectations module
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateGExpectationsModule:
    """Gate G: Verify expectations.py exists with non-empty expected-outputs."""

    def _make_exercise_dir(self, tmp_path: Path, slug: str) -> Path:
        return _make_checker_test_exercise_dir(tmp_path, slug)

    def test_missing_expectations_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        findings = verify_exercise_quality._check_expectations_module(exercise_dir, parts=1)
        assert len(findings) > 0
        assert any("expectations" in f.message and f.severity == "ERROR" for f in findings)

    def test_empty_dict_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        expectations_path = exercise_dir / "tests" / "expectations.py"
        expectations_path.parent.mkdir(parents=True, exist_ok=True)
        expectations_path.write_text(
            "EX004_EXPECTED_OUTPUTS: dict[int, str] = {}\n",
            encoding="utf-8",
        )

        findings = verify_exercise_quality._check_expectations_module(exercise_dir, parts=1)
        assert len(findings) > 0
        assert any("empty" in f.message.lower() for f in findings)

    def test_non_empty_expected_outputs_returns_no_finding(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        expectations_path = exercise_dir / "tests" / "expectations.py"
        expectations_path.parent.mkdir(parents=True, exist_ok=True)
        expectations_path.write_text(
            "EX004_EXPECTED_OUTPUTS: dict[int, str] = {1: 'Hello'}\n",
            encoding="utf-8",
        )

        findings = verify_exercise_quality._check_expectations_module(exercise_dir, parts=1)
        assert len(findings) == 0

    def test_missing_keys_for_all_parts_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        expectations_path = exercise_dir / "tests" / "expectations.py"
        expectations_path.parent.mkdir(parents=True, exist_ok=True)
        expectations_path.write_text(
            "EX004_EXPECTED_OUTPUTS: dict[int, str] = {1: 'Hello'}\n",
            encoding="utf-8",
        )

        # Set parts=3 in exercise.json
        meta_path = exercise_dir / "exercise.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["parts"] = 3
        meta_path.write_text(json.dumps(meta), encoding="utf-8")

        findings = verify_exercise_quality._check_expectations_module(exercise_dir, parts=3)
        assert len(findings) > 0
        assert any("1..3" in f.message or "parts" in f.message.lower() for f in findings)


# ═══════════════════════════════════════════════════════════════════════════════
# Gate G — expectations input() consistency (regression for hang-on-input)
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateGInputConsistency:
    """Cross-check that expectations.py input() classification matches notebook."""

    def _make_exercise_dir(self, tmp_path: Path, slug: str) -> Path:
        metadata: dict[str, int | str] = {
            **_exercise_metadata(slug),  # type: ignore[arg-type]
            "exercise_type": "modify",
            "parts": 3,
        }
        return _write_canonical_exercise(
            tmp_path,
            slug,
            metadata=metadata,
            include_explanation=False,
            missing_paths={"tests/expectations.py"},
        )

    def _write_expectations(
        self,
        ex_dir: Path,
        *,
        static_outputs: dict[int, str] | None = None,
        input_cases: dict[int, dict[str, object]] | None = None,
        derived_alias: bool = False,
    ) -> None:
        path = ex_dir / "tests" / "expectations.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = ["from __future__ import annotations\n", "from typing import Final\n"]
        if static_outputs is not None:
            lines.append(
                f"EX004_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {static_outputs!r}\n"
            )
        if input_cases is not None:
            lines.append(
                f"EX004_INPUT_CASES: Final[dict[int, dict[str, object]]] = {input_cases!r}\n"
            )
        if derived_alias:
            lines.append(
                "EX004_DERIVED_OUTPUTS: Final[dict[int, str]] = {\n"
                "    exercise_no: case['expected_output']\n"
                "    for exercise_no, case in EX004_INPUT_CASES.items()\n"
                "}\n"
            )
        path.write_text("".join(lines), encoding="utf-8")

    def _make_notebook_with_cells(self, cells_data: list[tuple[str, str]]) -> dict[str, Any]:
        """Build a notebook dict.  Each tuple is (tag, source_text)."""
        cells: list[dict[str, Any]] = []
        for tag, source in cells_data:
            cells.append(
                {
                    "cell_type": "code",
                    "metadata": {"language": "python", "tags": [tag]},
                    "source": [source],
                }
            )
        return {"cells": cells}

    def test_input_in_notebook_but_missing_from_input_cases_returns_error(
        self, tmp_path: Path
    ) -> None:
        """Exercise uses input() but is only in static outputs → ERROR."""
        slug = "ex004_sequence_modify_variables"
        ex_dir = self._make_exercise_dir(tmp_path, slug)
        self._write_expectations(
            ex_dir,
            static_outputs={1: "hello\n", 2: "world\n", 3: "static\n"},
        )
        nb_solution = self._make_notebook_with_cells(
            [
                ("exercise1", 'print("hello")\n'),
                ("exercise2", 'name = input("Name: ")\nprint(f"Hello {name}")\n'),
                ("exercise3", 'print("static")\n'),
            ]
        )

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=cast(verify_exercise_quality.NotebookDocument, nb_solution),
            parts=3,
        )
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) >= 1
        assert any(
            "Exercise 2" in e.message
            and "input()" in e.message.lower()
            and "hang" in e.message.lower()
            for e in errors
        ), f"Expected hang-warning for exercise 2, got: {[e.message for e in errors]}"

    def test_input_in_notebook_and_in_input_cases_returns_no_finding(self, tmp_path: Path) -> None:
        """Exercise uses input() and is correctly in INPUT_CASES → no finding."""
        slug = "ex004_sequence_modify_variables"
        ex_dir = self._make_exercise_dir(tmp_path, slug)
        self._write_expectations(
            ex_dir,
            static_outputs={1: "hello\n"},
            input_cases={2: {"inputs": ["Alice"], "expected_output": "Hello Alice\n"}},
        )
        nb_solution = self._make_notebook_with_cells(
            [
                ("exercise1", 'print("hello")\n'),
                ("exercise2", 'name = input("Name: ")\nprint(f"Hello {name}")\n'),
            ]
        )

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=cast(verify_exercise_quality.NotebookDocument, nb_solution),
            parts=2,
        )
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_no_input_in_notebook_but_in_input_cases_returns_error(self, tmp_path: Path) -> None:
        """Exercise does NOT use input() but is in INPUT_CASES → ERROR."""
        slug = "ex004_sequence_modify_variables"
        ex_dir = self._make_exercise_dir(tmp_path, slug)
        self._write_expectations(
            ex_dir,
            static_outputs={1: "hello\n"},
            input_cases={2: {"inputs": ["Alice"], "expected_output": "Hello Alice\n"}},
        )
        nb_solution = self._make_notebook_with_cells(
            [
                ("exercise1", 'print("hello")\n'),
                ("exercise2", 'print("world")\n'),
            ]
        )

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=cast(verify_exercise_quality.NotebookDocument, nb_solution),
            parts=2,
        )
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) >= 1
        assert any(
            "Exercise 2" in e.message and "does not use input()" in e.message.lower()
            for e in errors
        ), f"Expected error for exercise 2, got: {[e.message for e in errors]}"

    def test_all_static_exercises_with_no_input_returns_no_finding(self, tmp_path: Path) -> None:
        """All exercises are static and correctly in static outputs → no finding."""
        slug = "ex004_sequence_modify_variables"
        ex_dir = self._make_exercise_dir(tmp_path, slug)
        self._write_expectations(
            ex_dir,
            static_outputs={1: "a\n", 2: "b\n", 3: "c\n"},
        )
        nb_solution = self._make_notebook_with_cells(
            [
                ("exercise1", 'print("a")\n'),
                ("exercise2", 'print("b")\n'),
                ("exercise3", 'print("c")\n'),
            ]
        )

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=cast(verify_exercise_quality.NotebookDocument, nb_solution),
            parts=3,
        )
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_exercise_in_both_dicts_returns_warning(self, tmp_path: Path) -> None:
        """Exercise in both EX<N>_EXPECTED_OUTPUTS and INPUT_CASES → WARN."""
        slug = "ex004_sequence_modify_variables"
        ex_dir = self._make_exercise_dir(tmp_path, slug)
        self._write_expectations(
            ex_dir,
            static_outputs={1: "hello\n"},
            input_cases={1: {"inputs": ["x"], "expected_output": "hello\n"}},
        )
        nb_solution = self._make_notebook_with_cells(
            [("exercise1", 'name = input("Name: ")\nprint("hello")\n')]
        )

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=cast(verify_exercise_quality.NotebookDocument, nb_solution),
            parts=1,
        )
        warnings = [f for f in findings if f.severity == "WARN"]
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 0, f"Expected no errors, got: {errors}"
        assert any("listed in both" in w.message.lower() for w in warnings), (
            f"Expected both-dicts warning, got: {[w.message for w in warnings]}"
        )

    def test_derived_outputs_alias_overlapping_input_cases_returns_no_warning(
        self, tmp_path: Path
    ) -> None:
        """A *_DERIVED_OUTPUTS alias built from INPUT_CASES is not a real overlap.

        Regression test for the name filter in the expectations/input
        consistency check: without it, exercises such as ex004 (whose
        EX004_DERIVED_OUTPUTS comprehension repeats every INPUT_CASES key)
        get a spurious "listed in both" warning.
        """
        slug = "ex004_sequence_modify_variables"
        ex_dir = self._make_exercise_dir(tmp_path, slug)
        self._write_expectations(
            ex_dir,
            input_cases={1: {"inputs": ["x"], "expected_output": "hello\n"}},
            derived_alias=True,
        )
        nb_solution = self._make_notebook_with_cells(
            [("exercise1", 'name = input("Name: ")\nprint("hello")\n')]
        )

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=cast(verify_exercise_quality.NotebookDocument, nb_solution),
            parts=1,
        )
        warnings = [f for f in findings if f.severity == "WARN"]
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 0, f"Expected no errors, got: {errors}"
        assert not any("listed in both" in w.message.lower() for w in warnings), (
            f"Derived alias must not warn, got: {[w.message for w in warnings]}"
        )


class TestMainHangRegression:
    """Regression test: verify_exercise_quality skips Gate I when input-consistency
    errors would cause a hang.

    When expectations.py misclassifies an interactive exercise as static,
    calling run_cell_and_capture_output on that cell would block forever
    on input().  The fix: if _check_expectations_input_consistency returns
    any ERROR, main() skips _check_runtime_self_check (Gate I) entirely.
    """

    _SLUG = "ex014_sequence_gaps_regtest"

    @staticmethod
    def _make_exercise_cells() -> list[tuple[str, str]]:
        """Return (tag, source) for 3 exercise cells.

        exercise1: static (just print)
        exercise2: uses input() — the hang trigger
        exercise3: static (just print)
        """
        return [
            ("exercise1", 'print("static output")\n'),
            ("exercise2", 'name = input("Name: ")\nprint(f"Hello {name}")\n'),
            ("exercise3", 'print("also static")\n'),
        ]

    def _build_synthetic_exercise(
        self,
        tmp_path: Path,
        expectations_content: str,
    ) -> Path:
        """Create a complete synthetic exercise directory and return repo_root."""
        slug = self._SLUG
        repo_root = tmp_path / "repo"
        ex_dir = repo_root / "exercises" / "sequence" / slug

        # exercise.json
        make_exercise_json(
            ex_dir,
            {
                "schema_version": 1,
                "exercise_key": slug,
                "exercise_id": 14,
                "slug": slug,
                "title": "Hang Regression Test Exercise",
                "construct": "sequence",
                "exercise_type": "gaps",
                "parts": 3,
            },
        )

        # README.md
        (ex_dir / "README.md").write_text("# README\n", encoding="utf-8")

        # OrderOfTeaching.md
        _write_order_of_teaching(repo_root, slug)

        exercise_cells = self._make_exercise_cells()

        # Student notebook
        student_cells: list[dict[str, Any]] = []
        for tag, source in exercise_cells:
            student_cells.append(
                {
                    "cell_type": "code",
                    "metadata": {"language": "python", "tags": [tag]},
                    "source": [source],
                }
            )
        # Self-checker cell with student variant override
        student_cells.append(
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "import os\n",
                    'os.environ["PYTUTOR_ACTIVE_VARIANT"] = "student"\n',
                    "from exercise_runtime_support.student_checker import run_notebook_checks\n",
                    f"run_notebook_checks('{slug}')\n",
                ],
            }
        )
        _write_notebook_cells(ex_dir / "notebooks" / "student.ipynb", student_cells)

        # Solution notebook
        solution_cells: list[dict[str, Any]] = []
        for tag, source in exercise_cells:
            solution_cells.append(
                {
                    "cell_type": "code",
                    "metadata": {"language": "python", "tags": [tag]},
                    "source": [source],
                }
            )
        # Self-checker cell with solution variant override
        solution_cells.append(
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "import os\n",
                    'os.environ["PYTUTOR_ACTIVE_VARIANT"] = "solution"\n',
                    "from exercise_runtime_support.student_checker import run_notebook_checks\n",
                    f"run_notebook_checks('{slug}')\n",
                ],
            }
        )
        _write_notebook_cells(ex_dir / "notebooks" / "solution.ipynb", solution_cells)

        # tests/student_checker_support.py
        checker_path = ex_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "from __future__ import annotations\n"
            "from typing import Any\n"
            'CHECKS: list[Any] = [{"fake": "check"}]\n',
            encoding="utf-8",
        )

        # tests/expectations.py
        expectations_path = ex_dir / "tests" / "expectations.py"
        expectations_path.parent.mkdir(parents=True, exist_ok=True)
        expectations_path.write_text(expectations_content, encoding="utf-8")

        # tests/test_{slug}.py
        test_path = ex_dir / "tests" / f"test_{slug}.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("def test_placeholder() -> None:\n    assert True\n", encoding="utf-8")

        return repo_root

    def test_main_skips_gate_i_when_input_consistency_errors(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When expectations misclassifies an input()-using cell as static,
        main() must skip Gate I and emit a WARN instead of hanging."""
        expectations_content = (
            "from __future__ import annotations\n"
            "from typing import Final\n"
            "EX014_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {\n"
            '    1: "static output\\n",\n'
            '    2: "Hello Alice\\n",\n'  # exercise 2 uses input() but is in STATIC
            '    3: "also static\\n",\n'
            "}\n"
        )
        repo_root = self._build_synthetic_exercise(tmp_path, expectations_content)

        exit_code = verify_exercise_quality.main([self._SLUG, "--repo-root", str(repo_root)])
        captured = capsys.readouterr()
        combined = captured.out + captured.err

        # Must be non-zero (ERROR findings exist)
        assert exit_code != 0

        # Must contain the input-consistency ERROR for exercise 2 with "hang" message
        assert (
            "Exercise 2" in combined
            and "input()" in combined.lower()
            and "hang" in combined.lower()
        ), f"Missing hang-warning for exercise 2 in:\n{combined}"

        # Must contain the WARN about skipping Gate I
        assert "Skipping runtime self-check (Gate I)" in combined, (
            f"Missing Gate-I-skip warning in:\n{combined}"
        )

        # Must NOT contain a runtime self-check error (proving Gate I was skipped)
        assert (
            "Self-check failed" not in combined and "Runtime self-check raised" not in combined
        ), f"Gate I should have been skipped but found runtime self-check output:\n{combined}"

    def test_main_completes_normally_with_correct_expectations(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Positive control: when expectations are correct, the verifier
        completes normally — Gate I may produce errors but there is no hang."""
        expectations_content = (
            "from __future__ import annotations\n"
            "from typing import Final\n"
            "EX014_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {\n"
            '    1: "static output\\n",\n'
            '    2: "Hello Alice\\n",\n'
            '    3: "also static\\n",\n'
            "}\n"
            "EX014_INPUT_CASES: Final[dict[int, dict[str, object]]] = {\n"
            "    2: {'inputs': ['Alice'], 'expected_output': 'Hello Alice\\n'},\n"
            "}\n"
        )
        repo_root = self._build_synthetic_exercise(tmp_path, expectations_content)

        _ = verify_exercise_quality.main([self._SLUG, "--repo-root", str(repo_root)])
        captured = capsys.readouterr()
        combined = captured.out + captured.err

        # Must NOT contain the hang-related skip warning (Gate I was not
        # skipped due to input-consistency errors)
        assert "Skipping runtime self-check (Gate I)" not in combined, (
            f"Gate I should not have been skipped for correct expectations:\n{combined}"
        )

        # Must NOT contain the hang-related error
        assert "hang" not in combined.lower(), (
            f"No hang-related messages expected for correct expectations:\n{combined}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Gate H — Notebook variant overrides
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateHNotebookVariantOverrides:
    """Gate H: Verify variant overrides in student and solution notebooks.

    Policy: the student self-checker cell may omit the ``PYTUTOR_ACTIVE_VARIANT``
    assignment because the checker runtime already defaults to the student
    variant when the variable is unset.  An explicitly wrong student assignment
    stays a WARN, and a missing or wrong solution assignment stays an ERROR
    because that cell would otherwise read ``student.ipynb``.
    """

    def _make_notebook(self, source_lines: list[str]) -> dict[str, Any]:
        return {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {"language": "python"},
                    "source": source_lines,
                },
            ],
        }

    def _make_exercise_dir(self, tmp_path: Path, slug: str) -> Path:
        metadata = {
            **_exercise_metadata(slug),
            "exercise_type": "modify",
            "parts": 1,
        }
        exercise_dir = _write_canonical_exercise(
            tmp_path,
            slug,
            metadata=metadata,
            include_explanation=False,
        )
        return exercise_dir

    def test_student_missing_override_is_valid_when_solution_overrides(
        self,
        tmp_path: Path,
    ) -> None:
        """An omitted student override is valid, matching the runtime default."""
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook(["run_notebook_checks('ex004_sequence_modify_vars')\n"])
        solution_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'solution'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8"
        )
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8"
        )
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb"
        )
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb"
        )

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir,
            student_nb=nb_student,
            solution_nb=nb_solution,
        )
        assert findings == []

    def test_missing_student_override_does_not_mask_the_solution_error(
        self,
        tmp_path: Path,
    ) -> None:
        """A missing solution override is the only finding in the pair."""
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        bare_nb = self._make_notebook(["run_notebook_checks('ex004_sequence_modify_vars')\n"])
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(bare_nb), encoding="utf-8"
        )
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(bare_nb), encoding="utf-8"
        )
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb"
        )
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb"
        )

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir,
            student_nb=nb_student,
            solution_nb=nb_solution,
        )
        assert [f.severity for f in findings] == ["ERROR"]

    def test_student_wrong_variant_returns_warning(self, tmp_path: Path) -> None:
        """An explicitly wrong student override is never a silent pass."""
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'solution'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        solution_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'solution'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8"
        )
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8"
        )
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb"
        )
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb"
        )

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir,
            student_nb=nb_student,
            solution_nb=nb_solution,
        )
        assert [f.severity for f in findings] == ["WARN"]
        assert "instead of 'student'" in findings[0].message

    def test_solution_missing_variant_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        solution_nb = self._make_notebook(["run_notebook_checks('ex004_sequence_modify_vars')\n"])
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8"
        )
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8"
        )
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb"
        )
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb"
        )

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir,
            student_nb=nb_student,
            solution_nb=nb_solution,
        )
        assert len(findings) > 0
        assert any("solution" in f.message and f.severity == "ERROR" for f in findings)

    def test_solution_wrong_variant_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        solution_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8"
        )
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8"
        )
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb"
        )
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb"
        )

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir,
            student_nb=nb_student,
            solution_nb=nb_solution,
        )
        assert len(findings) > 0
        assert any("instead of 'solution'" in f.message and f.severity == "ERROR" for f in findings)

    def test_both_variants_correct_returns_no_finding(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        solution_nb = self._make_notebook(
            [
                "import os\n",
                "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'solution'\n",
                "run_notebook_checks('ex004_sequence_modify_vars')\n",
            ]
        )
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8"
        )
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8"
        )
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb"
        )
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb"
        )

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir,
            student_nb=nb_student,
            solution_nb=nb_solution,
        )
        assert len(findings) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Gate I — Runtime self-check
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateIRuntimeSelfCheck:
    """Gate I: Run self-checker against solution variant and report failures."""

    def test_valid_solution_returns_no_finding(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = tmp_path / "exercises" / "sequence" / slug
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "from __future__ import annotations\n"
            "from typing import Any\n"
            "CHECKS: list[Any] = [{'fake': 'check'}]\n",
            encoding="utf-8",
        )

        import types

        mock_result = types.SimpleNamespace()
        mock_result.passed = True
        mock_result.exercise_no = 1
        mock_result.title = "test"
        mock_result.issues = []

        monkeypatch.setattr(
            "exercise_runtime_support.student_checker.checks.run_exercise_checks",
            # type: ignore[reportUnknownLambdaType,reportUnknownArgumentType]
            lambda key: [mock_result],  # type: ignore[arg-type]
        )

        findings = verify_exercise_quality._check_runtime_self_check(
            ex_dir=exercise_dir,
            exercise_key=slug,
        )
        assert len(findings) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Section 1 — Filter progression scanning to only exerciseN tagged cells
# ═══════════════════════════════════════════════════════════════════════════════


class TestSection1ProgressionScanFiltering:
    """Tests for filtering _collect_code_cell_text to exerciseN tagged cells only."""

    def test_collect_code_cell_text_excludes_untagged_cells(
        self,
        tmp_path: Path,
    ) -> None:
        """Only exercise-tagged code cells should appear in the result."""
        cells: list[dict[str, object]] = [
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise1"]},
                "source": ["print('Hello')\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": ["x = 42\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "import os\n",
                    'os.environ["PYTUTOR_ACTIVE_VARIANT"] = "student"\n',
                    "run_notebook_checks('test')\n",
                ],
            },
        ]
        nb_path = tmp_path / "test.ipynb"
        _write_notebook_cells(nb_path, cells)
        nb = verify_exercise_quality._load_notebook(nb_path)

        result = verify_exercise_quality._collect_code_cell_text(nb)

        assert "print('Hello')" in result
        assert "x = 42" not in result
        assert "import os" not in result

    def test_collect_code_cell_text_includes_all_exerciseN_cells(
        self,
        tmp_path: Path,
    ) -> None:
        """All exerciseN tagged cells must be present in the combined result."""
        cells: list[dict[str, object]] = [
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise1"]},
                "source": ["print('one')\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise2"]},
                "source": ["print('two')\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise3"]},
                "source": ["print('three')\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": ["x = 0\n"],
            },
        ]
        nb_path = tmp_path / "test.ipynb"
        _write_notebook_cells(nb_path, cells)
        nb = verify_exercise_quality._load_notebook(nb_path)

        result = verify_exercise_quality._collect_code_cell_text(nb)

        assert "print('one')" in result
        assert "print('two')" in result
        assert "print('three')" in result
        assert "x = 0" not in result

    def test_collect_code_cell_text_excludes_explanationN_cells(
        self,
        tmp_path: Path,
    ) -> None:
        """Explanation markdown cells should be excluded by cell_type filter."""
        cells: list[dict[str, object]] = [
            {
                "cell_type": "markdown",
                "metadata": {"language": "markdown", "tags": ["explanation1"]},
                "source": ["What happened?\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise1"]},
                "source": ["print('Hello')\n"],
            },
        ]
        nb_path = tmp_path / "test.ipynb"
        _write_notebook_cells(nb_path, cells)
        nb = verify_exercise_quality._load_notebook(nb_path)

        result = verify_exercise_quality._collect_code_cell_text(nb)

        assert "What happened?" not in result
        assert "print('Hello')" in result

    def test_progression_scan_ignores_self_check_imports(
        self,
        tmp_path: Path,
    ) -> None:
        """Untagged self-check cells with import statements should not cause
        false-positive progression violations."""
        cells: list[dict[str, object]] = [
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "import os\n",
                    'os.environ["PYTUTOR_ACTIVE_VARIANT"] = "student"\n',
                    "from exercise_runtime_support.student_checker import run_notebook_checks\n",
                    "run_notebook_checks('test_exercise')\n",
                ],
            },
        ]
        nb_path = tmp_path / "test.ipynb"
        _write_notebook_cells(nb_path, cells)
        nb_student = verify_exercise_quality._load_notebook(nb_path)

        findings = verify_exercise_quality._collect_progression_findings(
            construct="sequence",
            nb_path=nb_path,
            nb_solution=None,
            nb_solution_path=tmp_path / "solution.ipynb",
            nb_student=nb_student,
        )

        assert len(findings) == 0

    def test_progression_scan_still_detects_real_violations(
        self,
        tmp_path: Path,
    ) -> None:
        """A real progression violation inside an exerciseN-tagged cell must
        still be detected — guards against over-filtering."""
        cells: list[dict[str, object]] = [
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise1"]},
                "source": ["def foo():\n    pass\n"],
            },
        ]
        nb_path = tmp_path / "test.ipynb"
        _write_notebook_cells(nb_path, cells)
        nb_student = verify_exercise_quality._load_notebook(nb_path)

        findings = verify_exercise_quality._collect_progression_findings(
            construct="sequence",
            nb_path=nb_path,
            nb_solution=None,
            nb_solution_path=tmp_path / "solution.ipynb",
            nb_student=nb_student,
        )

        # A function definition in a sequence exercise is a violation
        assert len(findings) > 0
        assert any("progression violation" in f.message for f in findings)

    def test_collect_code_cell_text_excludes_mixed_untagged_and_tagged(
        self,
        tmp_path: Path,
    ) -> None:
        """Untagged cells with progression-violating patterns must not affect
        the collected text."""
        cells: list[dict[str, object]] = [
            {
                "cell_type": "code",
                "metadata": {"language": "python", "tags": ["exercise1"]},
                "source": ["print('safe code')\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": ["def bad_func():\n    pass\n"],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": ["import sys\n"],
            },
        ]
        nb_path = tmp_path / "test.ipynb"
        _write_notebook_cells(nb_path, cells)
        nb = verify_exercise_quality._load_notebook(nb_path)

        result = verify_exercise_quality._collect_code_cell_text(nb)

        assert "print('safe code')" in result
        assert "bad_func" not in result
        assert "import sys" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# Section 2 — --skip-empty-checks flag
# ═══════════════════════════════════════════════════════════════════════════════


class TestSection2SkipEmptyChecks:
    """Gate F: --skip-empty-checks suppresses empty-CHECKS findings.

    The _check_student_checker_support() function accepts a skip_empty_checks
    kwarg.  When True, the empty-CHECKS error is suppressed so that Phase 1
    (notebook authoring) does not fail.  All other errors (missing file,
    unimportable module) are still reported.
    """

    def _make_exercise_dir(self, tmp_path: Path, slug: str) -> Path:
        return _make_checker_test_exercise_dir(tmp_path, slug)

    # ── Unit tests for _check_student_checker_support(..., skip_empty_checks=) ──

    def test_skip_empty_checks_suppresses_empty_checks(self, tmp_path: Path) -> None:
        """skip_empty_checks=True suppresses the empty-CHECKS error."""
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "from __future__ import annotations\nfrom typing import Any\nCHECKS: list[Any] = []\n",
            encoding="utf-8",
        )

        findings = verify_exercise_quality._check_student_checker_support(
            exercise_dir, skip_empty_checks=True
        )
        assert len(findings) == 0

    def test_skip_empty_checks_does_not_suppress_missing_file(self, tmp_path: Path) -> None:
        """skip_empty_checks=True still reports missing student_checker_support.py."""
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        # Deliberately NOT writing the checker file

        findings = verify_exercise_quality._check_student_checker_support(
            exercise_dir, skip_empty_checks=True
        )
        assert len(findings) > 0
        assert any(
            "Missing student_checker_support.py" in f.message and f.severity == "ERROR"
            for f in findings
        )

    def test_skip_empty_checks_does_not_suppress_unimportable_file(self, tmp_path: Path) -> None:
        """skip_empty_checks=True still reports an unimportable checker."""
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text("this is synta error!!!\n", encoding="utf-8")

        findings = verify_exercise_quality._check_student_checker_support(
            exercise_dir, skip_empty_checks=True
        )
        assert len(findings) > 0
        assert any(f.severity == "ERROR" for f in findings)

    def test_skip_empty_checks_non_empty_checks_still_pass(self, tmp_path: Path) -> None:
        """skip_empty_checks=True with valid CHECKS — no findings."""
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "CHECKS = [{'tag': 'exercise1', 'check': None}]\n",
            encoding="utf-8",
        )

        findings = verify_exercise_quality._check_student_checker_support(
            exercise_dir, skip_empty_checks=True
        )
        assert len(findings) == 0

    # ── Integration test ─────────────────────────────────────────────────────

    def test_main_respects_skip_empty_checks_flag(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``verify_exercise_quality.main`` produces no empty-CHECKS error in
        output when ``--skip-empty-checks`` is passed and the only error
        is an empty CHECKS list."""
        slug = "ex004_sequence_modify_variables"
        # Build a full canonical exercise, but skip the default non-empty
        # student_checker_support.py so we can write an empty-CHECKS variant.
        exercise_dir = _write_canonical_exercise(
            tmp_path,
            slug,
            metadata={
                **_exercise_metadata(slug),
                "exercise_type": "modify",
                "parts": 1,
            },
            include_explanation=False,
            missing_paths={"tests/student_checker_support.py"},
        )
        # Write student_checker_support.py with an empty CHECKS list.
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "from __future__ import annotations\nfrom typing import Any\nCHECKS: list[Any] = []\n",
            encoding="utf-8",
        )

        # Run the full verifier with --skip-empty-checks. Even though other
        # gates (H/I) may produce errors in this bare exercise environment,
        # the empty-CHECKS error from Gate F must be suppressed.
        _ = verify_exercise_quality.main(
            [
                slug,
                "--repo-root",
                str(tmp_path),
                "--construct",
                "sequence",
                "--type",
                "modify",
                "--skip-empty-checks",
            ]
        )
        captured = capsys.readouterr()

        # The empty-CHECKS error must not appear in output
        assert "CHECKS list in student_checker_support.py is empty" not in captured.out
        # File exists so missing-file error is absent (already tested by unit test)
        assert "Missing student_checker_support.py" not in captured.out


# ═══════════════════════════════════════════════════════════════════════════════
# Section 3 — `--all` whole-catalogue sweep
# ═══════════════════════════════════════════════════════════════════════════════

_DEFECTIVE_SLUG = "ex010_sequence_debug_alpha"
_HEALTHY_SLUG = "ex020_sequence_debug_beta"


def _sweep_metadata(slug: str, *, exercise_id: int) -> dict[str, int | str]:
    """Return exercise metadata with an explicit ``exercise_id``.

    Sweep fixtures need distinct ids so an ``exercise_id`` clash is never the
    reason a candidate discovery strategy is rejected.
    """
    return {**_exercise_metadata(slug), "exercise_id": exercise_id}


def _write_teaching_order(repo_root: Path, slugs: list[str]) -> None:
    """Write one construct teaching-order file listing every sweep exercise.

    ``_write_canonical_exercise`` rewrites this file per call, so multi-exercise
    sweeps must restate the full list once the fixtures exist.
    """
    order_path = repo_root / "exercises" / "sequence" / "OrderOfTeaching.md"
    order_path.parent.mkdir(parents=True, exist_ok=True)
    order_path.write_text("\n".join(slugs) + "\n", encoding="utf-8")


def _record_gate_i_calls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Stub Gate I so sweeps stay hermetic, and record the keys it self-checks.

    Gate I resolves exercise keys against the real repository, so an unmocked
    sweep would both leak real repository state into the fixtures and report
    "Unknown exercise key" for every synthetic exercise.  The recorded keys are
    the observable evidence that Gates F-I ran for each discovered exercise.
    """
    checked: list[str] = []
    passing = SimpleNamespace(passed=True, exercise_no=1, title="stub", issues=[])

    def _record(key: str) -> list[Any]:
        checked.append(key)
        return [passing]

    monkeypatch.setattr(
        "exercise_runtime_support.student_checker.checks.run_exercise_checks",
        _record,
    )
    return checked


def _heading_order(output: str, keys: list[str]) -> list[str]:
    """Return ``keys`` ordered by the position of their ``=== key ===`` heading.

    Raises:
        AssertionError: if a key has no explicit heading in ``output``.
    """
    positions: list[tuple[int, str]] = []
    for key in keys:
        heading = f"=== {key} ==="
        if heading not in output:
            raise AssertionError(f"missing heading {heading!r} in verifier output:\n{output}")
        positions.append((output.index(heading), key))
    return [key for _, key in sorted(positions)]


def _owning_exercise_key(output: str, marker: str, keys: list[str]) -> str:
    """Return the exercise key named most recently before ``marker`` in ``output``.

    Raises:
        AssertionError: if ``marker`` never appears, so a renamed or absent
            finding message fails with a readable diagnostic.
    """
    if marker not in output:
        raise AssertionError(f"marker {marker!r} not found in verifier output:\n{output}")
    position = output.index(marker)
    return max((output.rfind(key, 0, position), key) for key in keys)[1]


class TestSection3AllExercisesSweep:
    """``--all`` runs every gate for every exercise under ``exercises/<construct>/``."""

    def _run_sweep_with_metadata_defect(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
        metadata: dict[str, int | str],
    ) -> tuple[int, str, list[str]]:
        """Sweep a repo holding one metadata-defective and one healthy exercise.

        Returns:
            The sweep exit code, its stdout, and the Gate I exercise keys.
        """
        checked = _record_gate_i_calls(monkeypatch)
        _write_canonical_exercise(tmp_path, _DEFECTIVE_SLUG, metadata=metadata)
        _write_canonical_exercise(
            tmp_path,
            _HEALTHY_SLUG,
            metadata=_sweep_metadata(_HEALTHY_SLUG, exercise_id=20),
        )
        _write_teaching_order(tmp_path, [_DEFECTIVE_SLUG, _HEALTHY_SLUG])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        return exit_code, capsys.readouterr().out, checked

    def test_all_flag_runs_every_gate_for_every_discovered_exercise(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A structure failure in one exercise and a Gate F failure in another
        must both be reported, and Gate I must run for both — the sweep must
        not stop at the first exercise or run the gates for only one."""
        checked = _record_gate_i_calls(monkeypatch)
        missing_readme = "ex010_sequence_modify_alpha"
        empty_checks = "ex020_sequence_modify_beta"
        _write_canonical_exercise(
            tmp_path,
            missing_readme,
            metadata={**_sweep_metadata(missing_readme, exercise_id=10), "exercise_type": "modify"},
            missing_paths={"README.md"},
        )
        empty_dir = _write_canonical_exercise(
            tmp_path,
            empty_checks,
            metadata={**_sweep_metadata(empty_checks, exercise_id=20), "exercise_type": "modify"},
        )
        checker_path = empty_dir / "tests" / "student_checker_support.py"
        checker_path.write_text("CHECKS: list[object] = []\n", encoding="utf-8")
        _write_teaching_order(tmp_path, [missing_readme, empty_checks])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        keys = [missing_readme, empty_checks]
        assert exit_code != 0
        assert "Missing canonical file: README.md" in captured.out
        assert "CHECKS list in student_checker_support.py is empty" in captured.out
        assert _heading_order(captured.out, keys) == sorted(keys)
        assert sorted(checked) == sorted(keys)

    def test_all_exits_zero_when_every_exercise_is_clean(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A clean catalogue must sweep to exit 0 and still verify both exercises."""
        checked = _record_gate_i_calls(monkeypatch)
        first = "ex001_sequence_debug_alpha"
        second = "ex002_sequence_debug_beta"
        for slug, exercise_id in ((first, 1), (second, 2)):
            _write_canonical_exercise(
                tmp_path,
                slug,
                metadata=_sweep_metadata(slug, exercise_id=exercise_id),
            )
        _write_teaching_order(tmp_path, [first, second])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Missing canonical file" not in captured.out
        assert sorted(checked) == sorted([first, second])

    def test_all_exits_zero_when_only_warnings_are_reported(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Warnings alone must not fail the sweep."""
        checked = _record_gate_i_calls(monkeypatch)
        exercise_dir = _write_canonical_exercise(
            tmp_path,
            _DEFECTIVE_SLUG,
            metadata=_sweep_metadata(_DEFECTIVE_SLUG, exercise_id=10),
        )
        # An explicitly wrong student override triggers a Gate H WARN only.
        _write_notebook(exercise_dir / "notebooks" / "student.ipynb", variant="solution")
        _write_teaching_order(tmp_path, [_DEFECTIVE_SLUG])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        assert "WARN:" in captured.out
        assert "ERROR:" not in captured.out
        assert exit_code == 0
        assert checked == [_DEFECTIVE_SLUG]

    def test_all_labels_each_exercise_findings_with_its_exercise_key(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Each finding must be attributable to the exercise that produced it."""
        _record_gate_i_calls(monkeypatch)
        missing_readme = "ex010_sequence_modify_alpha"
        missing_expectations = "ex020_sequence_modify_beta"
        _write_canonical_exercise(
            tmp_path,
            missing_readme,
            metadata={
                **_sweep_metadata(missing_readme, exercise_id=10),
                "exercise_type": "modify",
            },
            missing_paths={"README.md"},
        )
        expectations_dir = _write_canonical_exercise(
            tmp_path,
            missing_expectations,
            metadata={
                **_sweep_metadata(missing_expectations, exercise_id=20),
                "exercise_type": "modify",
            },
        )
        (expectations_dir / "tests" / "expectations.py").unlink()
        _write_teaching_order(tmp_path, [missing_readme, missing_expectations])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        keys = [missing_readme, missing_expectations]
        assert exit_code != 0
        assert (
            _owning_exercise_key(captured.out, "Missing canonical file: README.md", keys)
            == missing_readme
        )
        assert (
            _owning_exercise_key(captured.out, "Missing expectations.py", keys)
            == missing_expectations
        )

    def test_all_orders_exercises_deterministically(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Exercises are reported in a stable, exercise_key-sorted order that
        does not depend on on-disk creation order."""
        _record_gate_i_calls(monkeypatch)
        exercises = {
            "ex010_sequence_debug_alpha": 10,
            "ex020_sequence_debug_gamma": 20,
            "ex030_sequence_debug_beta": 30,
        }
        for slug in sorted(exercises, reverse=True):
            _write_canonical_exercise(
                tmp_path,
                slug,
                metadata=_sweep_metadata(slug, exercise_id=exercises[slug]),
            )
        _write_teaching_order(tmp_path, list(exercises))

        keys = list(exercises)
        verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        first_run = _heading_order(capsys.readouterr().out, keys)
        verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        second_run = _heading_order(capsys.readouterr().out, keys)

        assert first_run == sorted(keys)
        assert second_run == first_run

    def test_all_reports_progression_violations_for_every_exercise(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Progression scanning must run per exercise, not once for the sweep."""
        checked = _record_gate_i_calls(monkeypatch)
        first = "ex010_sequence_modify_alpha"
        second = "ex020_sequence_modify_beta"
        for slug, exercise_id in ((first, 10), (second, 20)):
            exercise_dir = _write_canonical_exercise(
                tmp_path,
                slug,
                metadata={
                    **_sweep_metadata(slug, exercise_id=exercise_id),
                    "exercise_type": "modify",
                },
            )
            for variant in ("student", "solution"):
                _write_notebook(
                    exercise_dir / "notebooks" / f"{variant}.ipynb",
                    source="for index in range(3):\n    print(index)\n",
                    variant=variant,
                )
        _write_teaching_order(tmp_path, [first, second])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        # Two warnings per exercise: student and solution notebooks.
        keys = [first, second]
        assert captured.out.count("Possible progression violation") == 2 * len(keys)
        assert sorted(checked) == sorted(keys)
        assert exit_code == 0

    def test_all_reports_invalid_metadata_without_dropping_other_exercises(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An invalid exercise_type is reported for its own exercise and the
        healthy exercise is still verified in the same sweep."""
        exit_code, output, checked = self._run_sweep_with_metadata_defect(
            tmp_path,
            capsys,
            monkeypatch,
            {**_sweep_metadata(_DEFECTIVE_SLUG, exercise_id=10), "exercise_type": "invalid_type"},
        )

        assert exit_code != 0
        assert "must define a valid exercise_type" in output
        assert _DEFECTIVE_SLUG in output
        assert _HEALTHY_SLUG in output
        assert checked == [_HEALTHY_SLUG]

    def test_all_reports_missing_metadata_field_without_dropping_other_exercises(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A missing required metadata field is reported, not skipped silently.

        Metadata-driven catalogue discovery would raise on this fixture, so the
        sweep must load metadata per discovered directory and convert the
        failure into a finding.
        """
        metadata = _sweep_metadata(_DEFECTIVE_SLUG, exercise_id=10)
        del metadata["construct"]
        exit_code, output, checked = self._run_sweep_with_metadata_defect(
            tmp_path,
            capsys,
            monkeypatch,
            metadata,
        )

        assert exit_code != 0
        assert "is missing required fields" in output
        assert _DEFECTIVE_SLUG in output
        assert _HEALTHY_SLUG in output
        assert checked == [_HEALTHY_SLUG]

    def test_all_reports_missing_metadata_file_without_dropping_other_exercises(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An exercise with no exercise.json at all is still discovered.

        Discovery is directory-based, so the sweep must report the missing
        metadata against that exercise instead of skipping the directory; the
        healthy sibling is still verified in the same sweep.
        """
        checked = _record_gate_i_calls(monkeypatch)
        _write_canonical_exercise(
            tmp_path,
            _DEFECTIVE_SLUG,
            include_metadata=False,
        )
        _write_canonical_exercise(
            tmp_path,
            _HEALTHY_SLUG,
            metadata=_sweep_metadata(_HEALTHY_SLUG, exercise_id=20),
        )
        _write_teaching_order(tmp_path, [_DEFECTIVE_SLUG, _HEALTHY_SLUG])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        keys = [_DEFECTIVE_SLUG, _HEALTHY_SLUG]
        assert exit_code != 0
        assert "exercise.json not found" in captured.out
        assert _owning_exercise_key(captured.out, "exercise.json not found", keys) == (
            _DEFECTIVE_SLUG
        )
        assert _heading_order(captured.out, keys) == sorted(keys)
        assert _HEALTHY_SLUG in checked

    def test_all_skip_empty_checks_suppresses_only_the_empty_checks_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``--skip-empty-checks`` suppresses the empty-CHECKS error only.

        The same sweep still reports a genuine warning-only finding, and the
        aggregate exit code reflects the remaining (warning-only) result.
        """
        checked = _record_gate_i_calls(monkeypatch)
        empty_checks = "ex010_sequence_modify_alpha"
        healthy = "ex020_sequence_debug_beta"
        checker_dir = _write_canonical_exercise(
            tmp_path,
            empty_checks,
            metadata={
                **_sweep_metadata(empty_checks, exercise_id=10),
                "exercise_type": "modify",
            },
        )
        (checker_dir / "tests" / "student_checker_support.py").write_text(
            "CHECKS: list[object] = []\n",
            encoding="utf-8",
        )
        # An explicitly wrong student override is a genuine Gate H warning.
        _write_notebook(checker_dir / "notebooks" / "student.ipynb", variant="solution")
        _write_canonical_exercise(
            tmp_path,
            healthy,
            metadata=_sweep_metadata(healthy, exercise_id=20),
        )
        _write_teaching_order(tmp_path, [empty_checks, healthy])

        keys = [empty_checks, healthy]
        unsuppressed = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        unsuppressed_out = capsys.readouterr().out

        assert unsuppressed != 0
        assert "CHECKS list in student_checker_support.py is empty" in unsuppressed_out
        assert sorted(checked) == sorted(keys)

        suppressed = verify_exercise_quality.main(
            ["--all", "--repo-root", str(tmp_path), "--skip-empty-checks"]
        )
        suppressed_out = capsys.readouterr().out

        assert "CHECKS list in student_checker_support.py is empty" not in suppressed_out
        assert "ERROR:" not in suppressed_out
        assert "instead of 'student'" in suppressed_out
        assert (
            _owning_exercise_key(
                suppressed_out,
                "instead of 'student'",
                keys,
            )
            == empty_checks
        )
        assert suppressed == 0
        # The second sweep still ran Gates F-I for both exercises.
        assert sorted(checked[len(keys) :]) == sorted(keys)

    def test_all_continues_after_a_malformed_notebook(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """One exercise with invalid notebook JSON must not abort the sweep."""
        checked = _record_gate_i_calls(monkeypatch)
        before = "ex010_sequence_debug_alpha"
        broken = "ex020_sequence_debug_broken"
        after = "ex030_sequence_debug_gamma"
        for slug, exercise_id in ((before, 10), (broken, 20), (after, 30)):
            _write_canonical_exercise(
                tmp_path,
                slug,
                metadata=_sweep_metadata(slug, exercise_id=exercise_id),
            )
        broken_notebook = (
            tmp_path / "exercises" / "sequence" / broken / "notebooks" / "student.ipynb"
        )
        broken_notebook.write_text("{ not json", encoding="utf-8")
        _write_teaching_order(tmp_path, [before, broken, after])

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        assert exit_code != 0
        assert broken in captured.out
        assert "Invalid JSON in notebook" in captured.out or broken_notebook.name in captured.out
        # The sweep continued past the broken exercise and verified the next one.
        assert after in captured.out
        assert after in checked

    def test_all_reports_an_empty_exercises_tree(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An empty tree must not produce a vacuous passing sweep."""
        (tmp_path / "exercises").mkdir()

        exit_code = verify_exercise_quality.main(["--all", "--repo-root", str(tmp_path)])

        assert exit_code != 0
        assert "ERROR:" in capsys.readouterr().out

    def test_single_exercise_malformed_notebook_still_raises(
        self,
        tmp_path: Path,
    ) -> None:
        """Single-key mode retains its existing malformed-JSON failure contract."""
        slug = "ex010_sequence_debug_alpha"
        exercise_dir = _write_canonical_exercise(
            tmp_path,
            slug,
            metadata=_sweep_metadata(slug, exercise_id=10),
        )
        (exercise_dir / "notebooks" / "student.ipynb").write_text("{ not json", encoding="utf-8")

        with pytest.raises(SystemExit, match="Invalid JSON in notebook"):
            verify_exercise_quality.main([slug, "--repo-root", str(tmp_path)])

    def test_single_exercise_mode_still_verifies_only_the_named_exercise(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Adding ``--all`` must leave the single-exercise CLI untouched."""
        checked = _record_gate_i_calls(monkeypatch)
        clean = "ex010_sequence_debug_alpha"
        broken = "ex020_sequence_debug_broken"
        _write_canonical_exercise(
            tmp_path,
            clean,
            metadata=_sweep_metadata(clean, exercise_id=10),
        )
        _write_canonical_exercise(
            tmp_path,
            broken,
            metadata=_sweep_metadata(broken, exercise_id=20),
            missing_paths={"README.md"},
        )
        _write_teaching_order(tmp_path, [clean, broken])

        exit_code = verify_exercise_quality.main([clean, "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Missing canonical file" not in captured.out
        assert checked == [clean]

        exit_code = verify_exercise_quality.main([broken, "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        assert exit_code != 0
        assert "Missing canonical file: README.md" in captured.out
        assert checked == [clean, broken]


# ═══════════════════════════════════════════════════════════════════════════════
# Section 4 — Gate G expectation conventions in real use
#
# Every fixture below mirrors the shape of a shipped exercise's
# ``exercises/<construct>/<exercise_key>/tests/expectations.py``. The baseline
# ``verify_exercise_quality.py --all`` sweep reports 26 errors across 18
# exercises, 25 of which are Gate G findings that contradict exercises whose
# solution-variant pytest suite passes, because Gate G insists on one
# ``EX<N>_EXPECTED_OUTPUTS``-style dict keyed by every part. Real exercises
# split coverage across static, interactive, and shape-specific dicts instead.
# ═══════════════════════════════════════════════════════════════════════════════

_EX002_SLUG = "ex002_sequence_modify_basics"
_EX003_SEQUENCE_SLUG = "ex003_sequence_modify_variables"
_EX004_SEQUENCE_SLUG = "ex004_sequence_debug_syntax"
_EX005_SEQUENCE_SLUG = "ex005_sequence_debug_logic"
_EX006_SEQUENCE_SLUG = "ex006_sequence_modify_casting"
_EX008_SEQUENCE_SLUG = "ex008_sequence_make_consolidation"
_EX014_SLUG = "ex014_sequence_gaps_advanced_arithmetic"
_SELECTION_EX003_SLUG = "ex003_selection_modify_elif_boundaries"
_EX011_SEQUENCE_SLUG = "ex011_sequence_gaps_consolidation"


def _convention_exercise_dir(tmp_path: Path, slug: str, *, parts: int) -> Path:
    """Create an exercise directory with no ``expectations.py`` yet.

    Returns:
        The exercise directory, with valid metadata, notebooks, teaching order,
        and a ``student_checker_support.py`` so only the expectations gates vary.
    """
    return _write_canonical_exercise(
        tmp_path,
        slug,
        metadata={
            **_exercise_metadata(slug),  # type: ignore[arg-type]
            "exercise_type": "modify",
            "parts": parts,
        },
        include_explanation=False,
        missing_paths={"tests/expectations.py"},
    )


def _write_expectations_source(ex_dir: Path, source: str) -> Path:
    """Write an exercise-local ``expectations.py`` from raw module source.

    Raw source (rather than a repr'd dict) keeps the fixture faithful to the
    shipped files, which use ``Final[...]`` annotations, ``TypedDict`` cases,
    and dict comprehensions.

    Returns:
        The written ``expectations.py`` path.
    """
    path = ex_dir / "tests" / "expectations.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _tagged_notebook(*cells: tuple[str, str]) -> verify_exercise_quality.NotebookDocument:
    """Build a solution notebook document from ``(tag, source)`` code cells."""
    return cast(
        verify_exercise_quality.NotebookDocument,
        {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {"language": "python", "tags": [tag]},
                    "source": [source],
                }
                for tag, source in cells
            ]
        },
    )


_STATIC_CELL = 'print("static")\n'
_INPUT_CELL = 'name = input("Name: ")\nprint(f"Hello {name}")\n'


# ═══════════════════════════════════════════════════════════════════════════════
# Gate G — split static/interactive coverage is acknowledged
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateGSplitExpectationCoverage:
    """Gate G must accept exercised static, interactive, and split conventions.

    The baseline sweep rejects ``ex002``/``ex003``/``ex004``/``ex005`` with
    "expectations.py must define an EX<N>_EXPECTED_OUTPUTS or
    EX<N>_EXPECTED_STATIC_OUTPUTS dict" even though their solution-variant tests
    pass, and rejects ``ex006``/``ex007``/``ex008``/``ex009``/``ex010``/``ex013``/
    ``ex014`` with "missing keys for parts" even though their interactive parts
    are fully covered by a separate input-case dict.
    """

    @pytest.mark.parametrize(
        ("slug", "parts", "source"),
        [
            pytest.param(
                _EX002_SLUG,
                4,
                "from __future__ import annotations\n"
                "from typing import Final\n"
                "EX002_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {\n"
                '    1: "Hi there!",\n'
                '    2: "Bye",\n'
                "}\n"
                "EX002_EXPECTED_MULTI_LINE: Final[dict[int, list[str]]] = {\n"
                "    3: ['Total cost: 8', 'Thanks'],\n"
                "}\n"
                "EX002_EXPECTED_NUMERIC: Final[dict[int, int | float]] = {4: 7}\n"
                "EX002_EXPECTED_PRINT_CALLS: Final[dict[int, int]] = {1: 1, 2: 1, 3: 2, 4: 1}\n",
                id="ex002-split-by-output-shape",
            ),
            pytest.param(
                _EX003_SEQUENCE_SLUG,
                3,
                "from __future__ import annotations\n"
                "from typing import Final\n"
                "EX003_EXPECTED_STATIC_OUTPUT: Final[dict[int, str]] = {\n"
                '    1: "Hi there!",\n'
                '    2: "I enjoy coding lessons.",\n'
                "}\n"
                "EX003_EXPECTED_PROMPTS: Final[dict[int, list[str]]] = {\n"
                '    3: ["Type the name of your favourite fruit:", "Type one word:"],\n'
                "}\n"
                'EX003_EXPECTED_INPUT_MESSAGES: Final[dict[int, str]] = {3: "I like {value1}"}\n',
                id="ex003-singular-static-output-plus-prompts",
            ),
            pytest.param(
                _EX004_SEQUENCE_SLUG,
                2,
                "from __future__ import annotations\n"
                "from typing import Final\n"
                "EX004_MIN_EXPLANATION_LENGTH: Final[int] = 50\n"
                "EX004_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {1: 'Hello World!'}\n"
                "EX004_PROMPT_STRINGS: Final[dict[int, str]] = {2: 'How many apples?'}\n"
                'EX004_FORMAT_VALIDATION: Final[dict[int, str]] = {2: "You have 5 apples"}\n',
                id="ex004-single-line-plus-prompt-and-format",
            ),
            pytest.param(
                _EX005_SEQUENCE_SLUG,
                2,
                "from __future__ import annotations\n"
                "from typing import Final\n"
                "EX005_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {1: '50'}\n"
                "EX005_EXERCISE_INPUTS: Final[dict[int, list[str]]] = {2: ['Maria', 'Jones']}\n"
                "EX005_INPUT_PROMPTS: Final[dict[int, tuple[str, str]]] = {\n"
                "    2: ('Enter first name: ', 'Enter last name: '),\n"
                "}\n",
                id="ex005-single-line-plus-inputs-and-prompts",
            ),
            pytest.param(
                _EX006_SEQUENCE_SLUG,
                4,
                "from __future__ import annotations\n"
                "from typing import Final, NotRequired, TypedDict\n"
                "class Ex006InputExpectation(TypedDict):\n"
                "    inputs: list[str]\n"
                "    prompt_contains: str\n"
                "    output_contains: NotRequired[str]\n"
                "EX006_EXPECTED_OUTPUTS: Final[dict[int, str]] = {1: '15', 2: '6.0'}\n"
                "EX006_INPUT_EXPECTATIONS: Final[dict[int, Ex006InputExpectation]] = {\n"
                '    3: {"inputs": ["6"], "prompt_contains": "Enter number"},\n'
                '    4: {"inputs": ["1.5"], "prompt_contains": "Enter price"},\n'
                "}\n",
                id="ex006-static-plus-input-expectations",
            ),
            pytest.param(
                _EX008_SEQUENCE_SLUG,
                5,
                "from __future__ import annotations\n"
                "from typing import Final, TypedDict\n"
                "class Ex008InteractiveCase(TypedDict):\n"
                "    inputs: list[str]\n"
                "    expected_output: str\n"
                'EX008_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {1: "Welcome!", 2: "Snack box"}\n'
                "EX008_INTERACTIVE_CASES: Final[dict[int, list[Ex008InteractiveCase]]] = {\n"
                '    3: [{"inputs": ["Aisha", "drawing"], "expected_output": "Hello Aisha!"}],\n'
                '    4: [{"inputs": ["6", "3"], "expected_output": "Books read: 18"}],\n'
                '    5: [{"inputs": ["2.5", "3"], "expected_output": "Total distance: 7.5 km"}],\n'
                "}\n",
                id="ex008-static-plus-interactive-cases",
            ),
        ],
    )
    def test_exercised_expectation_conventions_cover_every_part(
        self,
        tmp_path: Path,
        slug: str,
        parts: int,
        source: str,
    ) -> None:
        """Static, interactive, and split dicts that jointly cover 1..parts pass."""
        ex_dir = _convention_exercise_dir(tmp_path, slug, parts=parts)
        _write_expectations_source(ex_dir, source)

        findings = verify_exercise_quality._check_expectations_module(ex_dir, parts=parts)

        assert findings == [], (
            f"{slug} expectations follow a shipped convention and cover 1..{parts}; "
            f"got: {[f'{f.severity}: {f.message}' for f in findings]}"
        )

    def test_part_covered_by_no_expectation_dict_still_errors(self, tmp_path: Path) -> None:
        """Widening coverage must not accept an undeclared part.

        Guards the ex008 convention: parts 1-2 and 3 are declared but part 4 is
        absent from both dicts, so Gate G must still report the gap.
        """
        ex_dir = _convention_exercise_dir(tmp_path, _EX008_SEQUENCE_SLUG, parts=4)
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final\n"
            "EX008_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {1: 'Welcome!', 2: 'Snack box'}\n"
            "EX008_INTERACTIVE_CASES: Final[dict[int, list[dict[str, object]]]] = {\n"
            '    3: [{"inputs": ["Aisha"], "expected_output": "Hello Aisha!"}],\n'
            "}\n",
        )

        findings = verify_exercise_quality._check_expectations_module(ex_dir, parts=4)

        errors = [f for f in findings if f.severity == "ERROR"]
        assert errors, f"expected an ERROR for the undeclared part, got: {findings}"
        assert "4" in errors[0].message, (
            f"the ERROR must name the undeclared part 4, got: {errors[0].message}"
        )

    def test_module_without_any_expectation_dict_still_errors(self, tmp_path: Path) -> None:
        """An expectations.py with no output/case dicts is still an error.

        Widening coverage must not accept placeholder-only modules.
        """
        ex_dir = _convention_exercise_dir(tmp_path, _EX003_SEQUENCE_SLUG, parts=3)
        expectations_path = _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final\n"
            "EX003_MIN_EXPLANATION_LENGTH: Final[int] = 50\n",
        )

        findings = verify_exercise_quality._check_expectations_module(ex_dir, parts=3)

        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 1, f"expected exactly one ERROR, got: {findings}"
        assert errors[0].path == expectations_path


# ═══════════════════════════════════════════════════════════════════════════════
# Gate G — alternate input-case conventions are recognised
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateGAlternateInputCaseConventions:
    """The input-consistency cross-check must accept every shipped convention.

    ``_check_expectations_input_consistency`` only recognises
    ``EX<N>_INPUT_CASES``, so the baseline sweep reports 14 false "uses input()
    ... missing from EX<N>_INPUT_CASES" errors for sequence ``ex003``/``ex004``/
    ``ex005``/``ex006``/``ex008``, whose interactive parts are fully declared
    under ``EX<N>_EXPECTED_PROMPTS``, ``EX<N>_PROMPT_STRINGS``,
    ``EX<N>_EXERCISE_INPUTS``, ``EX<N>_INPUT_EXPECTATIONS``, and
    ``EX<N>_INTERACTIVE_CASES`` respectively.
    """

    @pytest.mark.parametrize(
        ("slug", "source"),
        [
            pytest.param(
                _EX003_SEQUENCE_SLUG,
                "from __future__ import annotations\n"
                "from typing import Final\n"
                'EX003_EXPECTED_STATIC_OUTPUT: Final[dict[int, str]] = {1: "Hi there!"}\n'
                "EX003_EXPECTED_PROMPTS: Final[dict[int, list[str]]] = {\n"
                '    2: ["Which town do you like the most?", "Which country is it in?"],\n'
                "}\n"
                'EX003_EXPECTED_INPUT_MESSAGES: Final[dict[int, str]] = {2: "I would visit {town}"}\n',
                id="ex003-expected-prompts-and-input-messages",
            ),
            pytest.param(
                _EX004_SEQUENCE_SLUG,
                "from __future__ import annotations\n"
                "from typing import Final\n"
                "EX004_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {1: 'Hello World!'}\n"
                "EX004_PROMPT_STRINGS: Final[dict[int, str]] = {2: 'Enter your name:'}\n"
                'EX004_FORMAT_VALIDATION: Final[dict[int, str]] = {2: "My name is Alice"}\n',
                id="ex004-prompt-strings-and-format-validation",
            ),
            pytest.param(
                _EX005_SEQUENCE_SLUG,
                "from __future__ import annotations\n"
                "from typing import Final\n"
                "EX005_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {1: '50'}\n"
                "EX005_EXERCISE_INPUTS: Final[dict[int, list[str]]] = {2: ['16', 'Birmingham']}\n"
                "EX005_INPUT_PROMPTS: Final[dict[int, tuple[str, str]]] = {\n"
                "    2: ('Enter your age: ', 'Enter your city: '),\n"
                "}\n",
                id="ex005-exercise-inputs-and-input-prompts",
            ),
            pytest.param(
                _EX006_SEQUENCE_SLUG,
                "from __future__ import annotations\n"
                "from typing import Final, NotRequired, TypedDict\n"
                "class Ex006InputExpectation(TypedDict):\n"
                "    inputs: list[str]\n"
                "    prompt_contains: str\n"
                "    output_contains: NotRequired[str]\n"
                'EX006_EXPECTED_OUTPUTS: Final[dict[int, str]] = {1: "15"}\n'
                "EX006_INPUT_EXPECTATIONS: Final[dict[int, Ex006InputExpectation]] = {\n"
                '    2: {"inputs": ["6"], "prompt_contains": "Enter number"},\n'
                "}\n",
                id="ex006-input-expectations",
            ),
            pytest.param(
                _EX008_SEQUENCE_SLUG,
                "from __future__ import annotations\n"
                "from typing import Final, TypedDict\n"
                "class Ex008InteractiveCase(TypedDict):\n"
                "    inputs: list[str]\n"
                "    expected_output: str\n"
                'EX008_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {1: "Welcome!"}\n'
                "EX008_INTERACTIVE_CASES: Final[dict[int, list[Ex008InteractiveCase]]] = {\n"
                '    2: [{"inputs": ["Aisha", "drawing"], "expected_output": "Hello Aisha!"}],\n'
                "}\n",
                id="ex008-interactive-cases",
            ),
        ],
    )
    def test_interactive_part_declared_under_alternate_convention_returns_no_finding(
        self,
        tmp_path: Path,
        slug: str,
        source: str,
    ) -> None:
        """An input()-using part declared under a shipped convention is accepted."""
        ex_dir = _convention_exercise_dir(tmp_path, slug, parts=2)
        _write_expectations_source(ex_dir, source)
        nb_solution = _tagged_notebook(("exercise1", _STATIC_CELL), ("exercise2", _INPUT_CELL))

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=nb_solution,
            parts=2,
        )

        assert findings == [], (
            f"{slug} declares exercise 2 interactively under a shipped convention; "
            f"got: {[f'{f.severity}: {f.message}' for f in findings]}"
        )

    def test_static_part_declared_interactively_still_errors(self, tmp_path: Path) -> None:
        """Recognising more conventions must not excuse a genuine misclassification."""
        ex_dir = _convention_exercise_dir(tmp_path, _EX008_SEQUENCE_SLUG, parts=2)
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final, TypedDict\n"
            "class Ex008InteractiveCase(TypedDict):\n"
            "    inputs: list[str]\n"
            "    expected_output: str\n"
            'EX008_EXPECTED_STATIC_OUTPUTS: Final[dict[int, str]] = {1: "Welcome!"}\n'
            "EX008_INTERACTIVE_CASES: Final[dict[int, list[Ex008InteractiveCase]]] = {\n"
            '    2: [{"inputs": ["Aisha"], "expected_output": "Hello Aisha!"}],\n'
            "}\n",
        )
        nb_solution = _tagged_notebook(("exercise1", _STATIC_CELL), ("exercise2", _STATIC_CELL))

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=nb_solution,
            parts=2,
        )

        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 1, f"expected exactly one ERROR, got: {findings}"
        assert "Exercise 2" in errors[0].message
        assert "does not use input()" in errors[0].message


# ═══════════════════════════════════════════════════════════════════════════════
# Gate G — derived / reference output aliases are not double declarations
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateGReferenceOutputAliases:
    """A reference alias over INPUT_CASES is not a second static declaration.

    ``ex003_selection_modify_elif_boundaries`` builds
    ``EX003_EXPECTED_OUTPUTS`` as a comprehension over ``EX003_INPUT_CASES`` and
    documents it as "a quick reference ... used by the quality verifier (Gate G)".
    Every exercise in it is interactive, so the baseline sweep emits 10 spurious
    "is listed in both EX<N>_EXPECTED_OUTPUTS and EX<N>_INPUT_CASES" warnings.
    """

    @staticmethod
    def _write_all_interactive(ex_dir: Path) -> None:
        """Write the two-part all-interactive shape used by selection ex003."""
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final, TypedDict\n"
            "class Ex003InputCase(TypedDict):\n"
            "    inputs: list[str]\n"
            "    expected_output: str\n"
            "EX003_INPUT_CASES: Final[dict[int, Ex003InputCase]] = {\n"
            '    1: {"inputs": ["25"], "expected_output": "Enter your total spend: Standard"},\n'
            '    2: {"inputs": ["1"], "expected_output": "Small van for 1 passengers"},\n'
            "}\n"
            "EX003_EXPECTED_OUTPUTS: Final[dict[int, str]] = {\n"
            "    exercise_no: case['expected_output']\n"
            "    for exercise_no, case in EX003_INPUT_CASES.items()\n"
            "}\n"
            "EX003_EDGE_CASES: Final[dict[int, list[Ex003InputCase]]] = {1: [], 2: []}\n",
        )

    def test_reference_alias_over_input_cases_is_not_flagged_as_double_declared(
        self,
        tmp_path: Path,
    ) -> None:
        """The selection ex003 shape must not warn "listed in both"."""
        ex_dir = _convention_exercise_dir(tmp_path, _SELECTION_EX003_SLUG, parts=2)
        self._write_all_interactive(ex_dir)
        nb_solution = _tagged_notebook(("exercise1", _INPUT_CELL), ("exercise2", _INPUT_CELL))

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=nb_solution,
            parts=2,
        )

        assert findings == [], (
            "every exercise is interactive and EX003_EXPECTED_OUTPUTS only mirrors "
            "EX003_INPUT_CASES; got: "
            f"{[f'{f.severity}: {f.message}' for f in findings]}"
        )

    def test_genuine_double_declaration_still_warns(self, tmp_path: Path) -> None:
        """A static dict that contradicts the input case is still a double declaration."""
        ex_dir = _convention_exercise_dir(tmp_path, _SELECTION_EX003_SLUG, parts=1)
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final, TypedDict\n"
            "class Ex003InputCase(TypedDict):\n"
            "    inputs: list[str]\n"
            "    expected_output: str\n"
            "EX003_INPUT_CASES: Final[dict[int, Ex003InputCase]] = {\n"
            '    1: {"inputs": ["25"], "expected_output": "Enter your total spend: Standard"},\n'
            "}\n"
            "EX003_EXPECTED_OUTPUTS: Final[dict[int, str]] = {1: 'Something else entirely'}\n",
        )
        nb_solution = _tagged_notebook(("exercise1", _INPUT_CELL))

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=nb_solution,
            parts=1,
        )

        errors = [f for f in findings if f.severity == "ERROR"]
        warnings = [f for f in findings if f.severity == "WARN"]
        assert not errors, f"expected no ERROR, got: {errors}"
        assert len(warnings) == 1, f"expected exactly one WARN, got: {findings}"
        assert "listed in both" in warnings[0].message

    @pytest.mark.parametrize(
        "derived_value",
        [
            pytest.param(
                '"Different: " + case["expected_output"]',
                id="prefixed-expected-output",
            ),
            pytest.param(
                'case["inputs"][0]',
                id="different-case-field",
            ),
        ],
    )
    def test_comprehension_deriving_new_values_is_still_a_double_declaration(
        self,
        tmp_path: Path,
        derived_value: str,
    ) -> None:
        """Only a value-for-value mirror of the input cases is a reference alias.

        Both shapes key their entries from ``EX003_INPUT_CASES`` but derive
        something other than each case's ``expected_output``, so the dict is a
        second, independent static declaration and the overlap must still be
        reported. Guards the alias predicate against treating any mention of an
        input-case dict as a mirror.
        """
        parts = 2
        ex_dir = _convention_exercise_dir(tmp_path, _SELECTION_EX003_SLUG, parts=parts)
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final, TypedDict\n"
            "class Ex003InputCase(TypedDict):\n"
            "    inputs: list[str]\n"
            "    expected_output: str\n"
            "EX003_INPUT_CASES: Final[dict[int, Ex003InputCase]] = {\n"
            '    1: {"inputs": ["25"], "expected_output": "Enter your total spend: Standard"},\n'
            '    2: {"inputs": ["1"], "expected_output": "Small van for 1 passengers"},\n'
            "}\n"
            "EX003_EXPECTED_OUTPUTS: Final[dict[int, str]] = {\n"
            f"    exercise_no: {derived_value}\n"
            "    for exercise_no, case in EX003_INPUT_CASES.items()\n"
            "}\n",
        )
        nb_solution = _tagged_notebook(("exercise1", _INPUT_CELL), ("exercise2", _INPUT_CELL))

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=nb_solution,
            parts=parts,
        )

        errors = [f for f in findings if f.severity == "ERROR"]
        warnings = [f for f in findings if f.severity == "WARN"]
        assert not errors, f"expected no ERROR, got: {errors}"
        assert len(warnings) == parts, (
            f"expected one overlap WARN per part, got: "
            f"{[f'{f.severity}: {f.message}' for f in findings]}"
        )
        assert all("listed in both" in w.message for w in warnings)

    def test_edge_case_dict_alone_does_not_count_as_interactive_coverage(
        self,
        tmp_path: Path,
    ) -> None:
        """An edge-case dict must not stand in for the primary input-case dict.

        ``ex014_sequence_gaps_advanced_arithmetic`` pairs
        ``EX014_EDGE_CASES`` with ``EX014_INPUT_CASES``; a part declared only in
        the edge-case dict still has no runnable input case, so the unsafe-input
        error must stand.
        """
        ex_dir = _convention_exercise_dir(tmp_path, _EX014_SLUG, parts=2)
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final, TypedDict\n"
            "class Ex014InputCase(TypedDict):\n"
            "    inputs: list[str]\n"
            "    expected_output: str\n"
            "EX014_INPUT_CASES: Final[dict[int, Ex014InputCase]] = {\n"
            '    1: {"inputs": ["1", "2"], "expected_output": "Sum: 3"},\n'
            "}\n"
            "EX014_EDGE_CASES: Final[dict[int, list[Ex014InputCase]]] = {\n"
            '    2: [{"inputs": ["0", "0"], "expected_output": "Sum: 0"}],\n'
            "}\n",
        )
        nb_solution = _tagged_notebook(("exercise1", _INPUT_CELL), ("exercise2", _INPUT_CELL))

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=nb_solution,
            parts=2,
        )

        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 1, f"expected exactly one ERROR, got: {findings}"
        assert "Exercise 2" in errors[0].message
        assert "input()" in errors[0].message


# ═══════════════════════════════════════════════════════════════════════════════
# Retained contract — genuine unsafe input() with no inputs still errors
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnsafeInputWithoutInputsIsStillAnError:
    """Widening recognition must not defuse the hang guard.

    The Gate I skip exists because ``run_cell_and_capture_output`` supplies no
    stdin, so an ``input()``-using cell classified as static blocks forever.
    An exercise with no runnable input case at all must keep reporting that
    error and keep Gate I skipped, under both the ``_OUTPUTS`` and the
    shape-specific static conventions.
    """

    def test_no_input_case_dict_reports_unsafe_input(self, tmp_path: Path) -> None:
        """A static-only module with an input()-using cell is still an ERROR."""
        ex_dir = _convention_exercise_dir(tmp_path, _EX004_SEQUENCE_SLUG, parts=1)
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final\n"
            "EX004_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {1: 'Hello Alice'}\n",
        )
        nb_solution = _tagged_notebook(("exercise1", _INPUT_CELL))

        findings = verify_exercise_quality._check_expectations_input_consistency(
            ex_dir=ex_dir,
            nb_solution=nb_solution,
            parts=1,
        )

        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) == 1, f"expected exactly one ERROR, got: {findings}"
        assert "Exercise 1" in errors[0].message
        assert "input()" in errors[0].message

    def test_main_still_errors_and_skips_gate_i_under_split_convention(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """End to end: the error, the Gate I skip, and no Gate I run all remain."""
        slug = "ex014_sequence_gaps_regtest2"
        repo_root = tmp_path / "repo"
        ex_dir = repo_root / "exercises" / "sequence" / slug
        make_exercise_json(
            ex_dir,
            {
                "schema_version": 1,
                "exercise_key": slug,
                "exercise_id": 14,
                "slug": slug,
                "title": "Unsafe Input Regression",
                "construct": "sequence",
                "exercise_type": "gaps",
                "parts": 1,
            },
        )
        (ex_dir / "README.md").write_text("# README\n", encoding="utf-8")
        _write_order_of_teaching(repo_root, slug)
        for variant in ("student", "solution"):
            _write_notebook(
                ex_dir / "notebooks" / f"{variant}.ipynb",
                include_explanation=False,
                source=_INPUT_CELL,
                variant=variant,
            )
        test_path = ex_dir / "tests" / f"test_{slug}.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("def test_placeholder() -> None:\n    assert True\n", encoding="utf-8")
        (ex_dir / "tests" / "student_checker_support.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Any\n"
            'CHECKS: list[Any] = [{"fake": "check"}]\n',
            encoding="utf-8",
        )
        # Split static convention with no runnable input case for the input() cell.
        _write_expectations_source(
            ex_dir,
            "from __future__ import annotations\n"
            "from typing import Final\n"
            "EX014_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {1: 'Hello Alice'}\n",
        )

        exit_code = verify_exercise_quality.main([slug, "--repo-root", str(repo_root)])
        captured = capsys.readouterr()
        combined = captured.out + captured.err

        assert exit_code != 0
        assert "Exercise 1 uses input()" in combined
        assert "Skipping runtime self-check (Gate I)" in combined
        assert "Self-check failed" not in combined
        assert "Runtime self-check raised" not in combined


# ═══════════════════════════════════════════════════════════════════════════════
# Desired contract — ex011 expectations.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestEx011ExpectationsModule:
    """``ex011_sequence_gaps_consolidation`` must ship a complete expectations.py.

    ex011 keeps its expected-output tables private inside
    ``tests/student_checker_support.py`` and repeats them again in the canonical
    test file, so the exercise has no exercise-local expectations module: Gate G
    reports ``Missing expectations.py``, the one ERROR in the ``--all`` sweep.

    The desired state is the ordinary one — a ``tests/expectations.py`` that
    declares every part, so Gate G reports nothing and no expectation data lives
    in a private checker dict.
    """

    def test_ex011_ships_a_complete_expectations_module(self, repo_root: Path) -> None:
        """Gate G reports no finding for ex011: the module exists and covers 1..parts."""
        ex_dir = repo_root / "exercises" / "sequence" / _EX011_SEQUENCE_SLUG
        metadata = json.loads((ex_dir / "exercise.json").read_text(encoding="utf-8"))
        parts = int(metadata["parts"])

        findings = verify_exercise_quality._check_expectations_module(
            ex_dir,
            parts=parts,
        )

        assert findings == [], (
            f"{_EX011_SEQUENCE_SLUG} must ship tests/expectations.py declaring every "
            f"part 1..{parts}; Gate G findings: "
            + "; ".join(f"{f.severity}: {f.message}" for f in findings)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Section 4 — Progression scan: executable constructs, not printed token text
# ═══════════════════════════════════════════════════════════════════════════════
#
# Batch 3 policy (REMAINING_WORK.md, "Batch 3"), stated here as the desired
# contract so the green phase has one authoritative statement to implement.
#
# 1. The scan reports a later construct only where it is *executable* in a
#    tagged ``exerciseN`` code cell.  Token text inside comments, ordinary
#    string literals, and the literal parts of f-strings is printed prose
#    rather than student code, so it must not warn.  Real occurrences in this
#    repository include ``# Use // for full hours and % for leftover minutes``
#    (sequence ex012, ex015), ``print("Good try")`` (selection ex002), and
#    ``print(f"Standard delivery for £{total} order")`` (selection ex003).
#    The complementary boundary is an f-string *replacement field*: the
#    expression in ``print(f"{len([1, 2])} items")`` is executable and must
#    still warn, so the literal text and the expression cannot be treated alike.
# 2. A tagged debug cell may intentionally contain invalid syntax — 16 such
#    cells exist today, for example ``print("Hello World!"`` in sequence ex004 —
#    so the scan must not assume a tagged cell parses, and it must not skip a
#    whole cell that fails to parse either: real later-construct use in broken
#    debug code must still warn.
# 3. Casting is a documented prerequisite rather than a progression violation:
#    ``int()``, ``float()``, and ``str()`` calls are permitted in the
#    ``sequence`` and ``selection`` constructs, because ``input()`` always
#    returns ``str``.  This is a narrow waiver: iteration and real exception
#    handling stay forbidden in those constructs, and every other later
#    construct (lists, dictionaries, functions, file handling, libraries, oop)
#    stays exactly as strict as before.
#
# Every test below is written against that contract.  Both the student and the
# solution notebook surface are scanned, so a finding on either side fails.

#: ``_scan_both_variants`` scans a student and a solution notebook, so a single
#: offending cell is counted once per surface and this is the total to expect.
#: A cell that violates two distinct later constructs yields twice this.
_FINDINGS_BOTH_VARIANTS = 2


def _tagged_code_cell(tag: str, source: str) -> dict[str, Any]:
    """Build one ``exerciseN``-tagged code cell."""
    return {
        "cell_type": "code",
        "metadata": {"language": "python", "tags": [tag]},
        "source": [source],
    }


def _scan_both_variants(
    tmp_path: Path,
    *,
    construct: str,
    cells: list[dict[str, Any]],
) -> list[verify_exercise_quality.Finding]:
    """Scan ``cells`` through both the student and the solution notebook surface.

    Both variants receive identical tagged cells, so an unwanted warning on
    either surface fails the caller's assertion, and a wanted warning is
    reported once per notebook.
    """
    student_path = tmp_path / "student.ipynb"
    solution_path = tmp_path / "solution.ipynb"
    _write_notebook_cells(student_path, cells)
    _write_notebook_cells(solution_path, cells)
    return verify_exercise_quality._collect_progression_findings(
        construct=construct,
        nb_path=student_path,
        nb_solution=verify_exercise_quality._load_notebook(solution_path),
        nb_solution_path=solution_path,
        nb_student=verify_exercise_quality._load_notebook(student_path),
    )


def _finding_report(findings: list[verify_exercise_quality.Finding]) -> str:
    """Render findings for an assertion message."""
    return "; ".join(f"{f.severity}: {f.message}" for f in findings)


class TestProgressionScanExecutableConstructs:
    """Executable later constructs must still warn — over-filtering guard.

    These tests pass before and after the Batch 3 change; they exist so a
    fix that silences the false positives cannot also silence the real signal.
    """

    @pytest.mark.parametrize(
        ("construct", "source"),
        [
            ("sequence", "for hour in range(3):\n    print(hour)\n"),
            ("sequence", "count = 0\nwhile count < 3:\n    count = count + 1\n"),
            ("sequence", "for hour in range(3):\n    break\n"),
            ("sequence", "for hour in range(3):\n    continue\n"),
            ("selection", "for hour in range(3):\n    print(hour)\n"),
            ("selection", "count = 0\nwhile count < 3:\n    count = count + 1\n"),
            ("sequence", "try:\n    print(1)\nexcept ValueError:\n    print(2)\n"),
            ("sequence", 'raise ValueError("bad")\n'),
            ("selection", "try:\n    print(1)\nexcept ValueError:\n    print(2)\n"),
            ("sequence", "print(len([1, 2]))\n"),
            ("sequence", "import os\n"),
            ("sequence", 'items = {"a": 1}\nprint(items.get("a"))\n'),
            # A construct inside an f-string replacement field is executable, so
            # it must warn even though the surrounding literal text must not.
            ("sequence", 'print(f"{len([1, 2])} items")\n'),
            ("sequence", "flag = True\nprint(f\"{'yes' if flag else 'no'}\")\n"),
        ],
    )
    def test_executable_later_construct_still_warns(
        self,
        tmp_path: Path,
        construct: str,
        source: str,
    ) -> None:
        """One later construct in executable source warns once per notebook."""
        findings = _scan_both_variants(
            tmp_path,
            construct=construct,
            cells=[_tagged_code_cell("exercise1", source)],
        )

        assert len(findings) == _FINDINGS_BOTH_VARIANTS, (
            f"{construct!r} cell must warn once on each notebook surface; got "
            f"{len(findings)}: {_finding_report(findings)}"
        )
        assert all("progression violation" in f.message for f in findings)

    @pytest.mark.parametrize(
        ("construct", "source"),
        [
            ("sequence", "for hour in range(3)\n    print(hour)\n"),
            ("sequence", "count = 0\nwhile count < 3\n    count = count + 1\n"),
            ("selection", "for hour in range(3)\n    print(hour)\n"),
            ("selection", "count = 0\nwhile count < 3\n    count = count + 1\n"),
            ("sequence", "try\n    print(1)\nexcept ValueError:\n    print(2)\n"),
        ],
    )
    def test_unparsable_debug_cell_with_executable_later_construct_still_warns(
        self,
        tmp_path: Path,
        construct: str,
        source: str,
    ) -> None:
        """A cell that does not parse must be scanned, not skipped whole.

        Debug exercises ship intentionally broken tagged cells, so ignoring a
        cell because it fails to parse would drop genuine later-construct use.
        """
        # Fixture guard: confirm the cell really is invalid syntax.
        with pytest.raises(SyntaxError):
            ast.parse(source)

        findings = _scan_both_variants(
            tmp_path,
            construct=construct,
            cells=[_tagged_code_cell("exercise1", source)],
        )

        assert len(findings) == _FINDINGS_BOTH_VARIANTS, (
            f"{construct!r} debug cell must warn despite invalid syntax; got "
            f"{len(findings)}: {_finding_report(findings)}"
        )


class TestProgressionScanIgnoresNonExecutableTokenText:
    """Later-construct tokens in comments and string literals must not warn.

    The scanner currently regex-matches the concatenated tagged cell source as
    plain text, so every case below is a false positive today.
    """

    @pytest.mark.parametrize(
        ("construct", "source", "origin"),
        [
            (
                "sequence",
                "# Use // for full hours and % for leftover minutes\nhours = 7\nprint(hours)\n",
                "iteration 'for' inside a comment",
            ),
            (
                "sequence",
                "# Ask for input, convert, calculate, and print.\nn = 1\nprint(n)\n",
                "iteration 'for' inside a comment",
            ),
            (
                "selection",
                "# Try the elif branch for free delivery.\nfree = True\nprint(free)\n",
                "iteration 'for' and exceptions 'try' inside a comment",
            ),
            (
                "sequence",
                'print("Tip percentage (e.g. 10 for 10%):")\n',
                "iteration 'for' inside an ordinary string literal",
            ),
            (
                "sequence",
                'total = 1\nprint(f"Standard delivery for £{total} order")\n',
                "iteration 'for' inside an f-string literal",
            ),
            (
                "selection",
                'n = 1\nprint(f"Small van for {n} passengers")\n',
                "iteration 'for' inside an f-string literal",
            ),
            (
                "sequence",
                'print("Good try")\n',
                "exceptions 'try' inside an ordinary string literal",
            ),
            (
                "selection",
                'score = 1\nprint(f"Good try, {score}")\n',
                "exceptions 'try' inside an f-string literal",
            ),
        ],
    )
    def test_non_executable_token_text_does_not_warn(
        self,
        tmp_path: Path,
        construct: str,
        source: str,
        origin: str,
    ) -> None:
        """Comments and printed string text are prose, not student code."""
        findings = _scan_both_variants(
            tmp_path,
            construct=construct,
            cells=[_tagged_code_cell("exercise1", source)],
        )

        assert findings == [], (
            f"{construct!r} cell with {origin} must not warn; got {_finding_report(findings)}"
        )

    def test_invalid_debug_cell_with_tokens_only_in_text_does_not_warn(
        self,
        tmp_path: Path,
    ) -> None:
        """A deliberately broken debug cell must not warn on prose tokens.

        Debug exercises ship intentionally invalid tagged cells, so a scanner
        that assumes every tagged cell parses cannot be the basis of the fix.
        """
        source = (
            '# Reminder: a for loop and try/except come later in the course.\nprint("Good try"\n'
        )
        # Fixture guard: confirm the cell really is invalid syntax, so this
        # test cannot pass merely because the source happens to parse.
        with pytest.raises(SyntaxError):
            ast.parse(source)

        findings = _scan_both_variants(
            tmp_path,
            construct="sequence",
            cells=[_tagged_code_cell("exercise1", source)],
        )

        assert findings == [], (
            "an invalid debug cell whose later-construct tokens appear only in a "
            f"comment and a string literal must not warn; got {_finding_report(findings)}"
        )

    def test_compliant_cell_next_to_offending_cell_does_not_add_a_finding(
        self,
        tmp_path: Path,
    ) -> None:
        """A compliant cell beside an offending one adds no extra finding.

        This counts findings; it does **not** attribute them to a cell, because
        ``Finding`` carries only severity, message, and notebook path with no
        cell tag.  It therefore shows that the compliant cell contributes
        nothing beyond the single warning the offending cell already raises on
        each notebook surface, and nothing more than that.
        """
        cells = [
            _tagged_code_cell("exercise1", "for hour in range(3):\n    print(hour)\n"),
            _tagged_code_cell(
                "exercise2",
                "# Ask for input, convert, calculate, and print.\nn = 1\nprint(n)\n",
            ),
        ]

        findings = _scan_both_variants(tmp_path, construct="sequence", cells=cells)

        assert len(findings) == _FINDINGS_BOTH_VARIANTS, (
            "the compliant cell must add no finding beyond the offending cell's, "
            f"counted once per notebook surface; got {len(findings)}: "
            f"{_finding_report(findings)}"
        )


# A run of Unicode line separators long enough that an offset table built with
# ``str.splitlines`` (which also breaks on U+2028) misses the row after it
# entirely, instead of drifting by a character or two.
_UNICODE_SEPARATOR_ROW = "\u2028" * 40 + "\n"


class TestProgressionScanTokenizerLineOffsets:
    """Comment masking must follow the tokenizer's line boundaries.

    ``tokenize`` reads source with ``readline``, which ends a line only at a
    newline, so the mask offsets have to be built the same way.
    """

    def test_unicode_separator_row_does_not_shift_comment_masking(
        self,
        tmp_path: Path,
    ) -> None:
        """A comment after a Unicode separator row is prose and must not warn."""
        findings = _scan_both_variants(
            tmp_path,
            construct="sequence",
            cells=[
                _tagged_code_cell(
                    "exercise1",
                    f"n = 1\n{_UNICODE_SEPARATOR_ROW}# Reminder: a for loop comes later\n",
                )
            ],
        )

        assert findings == [], (
            "a comment after a Unicode line-separator row must still be blanked out; got "
            f"{_finding_report(findings)}"
        )

    def test_unicode_separator_row_keeps_executable_constructs(
        self,
        tmp_path: Path,
    ) -> None:
        """A real later construct after a Unicode separator row must still warn."""
        findings = _scan_both_variants(
            tmp_path,
            construct="sequence",
            cells=[
                _tagged_code_cell(
                    "exercise1",
                    f"n = 1\n{_UNICODE_SEPARATOR_ROW}for hour in range(3):\n    print(hour)\n",
                )
            ],
        )

        assert len(findings) == _FINDINGS_BOTH_VARIANTS, (
            "an executable loop after a Unicode line-separator row must warn once per "
            f"notebook surface; got {len(findings)}: {_finding_report(findings)}"
        )


class TestProgressionCastingPrerequisitePolicy:
    """``int``/``float``/``str`` casts are a permitted sequence/selection prerequisite."""

    @pytest.mark.parametrize(
        ("construct", "source"),
        [
            ("sequence", 'n = int(input("Enter a number: "))\nprint(n)\n'),
            ("sequence", 'n = float(input("Enter a number: "))\nprint(n)\n'),
            ("sequence", "n = 1\nprint(str(n))\n"),
            ("selection", 'n = int(input("Enter a number: "))\nif n > 10:\n    print("big")\n'),
            (
                "selection",
                'n = float(input("Enter a number: "))\nif n > 1.5:\n    print("big")\n',
            ),
            ("selection", "n = 1\nif n > 0:\n    print(str(n))\n"),
            ("sequence", 'n = "7"\nprint(f"{int(n)} plus one")\n'),
        ],
    )
    def test_documented_casting_prerequisite_does_not_warn(
        self,
        tmp_path: Path,
        construct: str,
        source: str,
    ) -> None:
        """Casting taught before selection must not be reported as progression."""
        findings = _scan_both_variants(
            tmp_path,
            construct=construct,
            cells=[_tagged_code_cell("exercise1", source)],
        )

        assert findings == [], (
            f"{construct!r} cell may cast with int()/float()/str(); got {_finding_report(findings)}"
        )

    @pytest.mark.parametrize(
        ("construct", "source"),
        [
            ("sequence", "for hour in range(3):\n    print(hour)\n"),
            ("selection", "for hour in range(3):\n    print(hour)\n"),
            ("sequence", "count = 0\nwhile count < 3:\n    count = count + 1\n"),
            ("selection", "count = 0\nwhile count < 3:\n    count = count + 1\n"),
            ("sequence", "try:\n    print(1)\nexcept ValueError:\n    print(2)\n"),
            ("selection", "try:\n    print(1)\nexcept ValueError:\n    print(2)\n"),
            ("sequence", 'raise ValueError("bad")\n'),
        ],
    )
    def test_prerequisite_waiver_excludes_iteration_and_exceptions(
        self,
        tmp_path: Path,
        construct: str,
        source: str,
    ) -> None:
        """The casting waiver is narrow: iteration and real handling still warn."""
        findings = _scan_both_variants(
            tmp_path,
            construct=construct,
            cells=[_tagged_code_cell("exercise1", source)],
        )

        assert len(findings) == _FINDINGS_BOTH_VARIANTS, (
            f"{construct!r} cell must still warn for iteration or exceptions, once per "
            f"notebook surface; got {len(findings)}: {_finding_report(findings)}"
        )
