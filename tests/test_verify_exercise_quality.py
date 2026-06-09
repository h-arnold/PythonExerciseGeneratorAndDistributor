from __future__ import annotations

import json
from pathlib import Path
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
            "source": ["print('Hello')\n"],
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
