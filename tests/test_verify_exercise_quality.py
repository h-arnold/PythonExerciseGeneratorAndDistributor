from __future__ import annotations

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
    """Gate H: Verify variant overrides in student and solution notebooks."""

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

    def test_student_missing_variant_returns_warning(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        nb = self._make_notebook(["run_notebook_checks('ex004_sequence_modify_vars')\n"])
        (exercise_dir / "notebooks" / "student.ipynb").write_text(json.dumps(nb), encoding="utf-8")
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(json.dumps(nb), encoding="utf-8")
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
        assert any("PYTUTOR_ACTIVE_VARIANT" in f.message for f in findings)

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
        # A student notebook without the variant override triggers a Gate H WARN only.
        _write_notebook(exercise_dir / "notebooks" / "student.ipynb", variant=None)
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
        # A student notebook without the variant override is a genuine Gate H warning.
        _write_notebook(checker_dir / "notebooks" / "student.ipynb", variant=None)
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
        assert "does not set PYTUTOR_ACTIVE_VARIANT" in suppressed_out
        assert (
            _owning_exercise_key(
                suppressed_out,
                "does not set PYTUTOR_ACTIVE_VARIANT",
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
