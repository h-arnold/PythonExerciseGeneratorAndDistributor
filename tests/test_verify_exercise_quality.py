from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import verify_exercise_quality
from tests.exercise_metadata_helpers import make_exercise_json


def _write_notebook(
    path: Path, *, include_explanation: bool = True,
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
                    "from exercise_runtime_support.student_checker import "
                    "run_notebook_checks\n",
                    "run_notebook_checks('placeholder')\n",
                ],
            }
        )

    notebook = {"cells": cells}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook), encoding="utf-8")


def _write_notebook_cells(path: Path, cells: list[dict[str, object]]) -> None:
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


class TestGateFStudentCheckerSupport:
    """Gate F: Verify student_checker_support.py exists with non-empty CHECKS."""

    def _make_exercise_dir(self, tmp_path: Path, slug: str) -> Path:
        metadata = {
            **_exercise_metadata(slug),
            "exercise_type": "modify",
            "parts": 1,
        }
        return _write_canonical_exercise(
            tmp_path, slug,
            metadata=metadata,
            include_explanation=False,
            missing_paths={"tests/student_checker_support.py", "tests/expectations.py"},
        )

    def test_missing_checker_support_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        findings = verify_exercise_quality._check_student_checker_support(exercise_dir)
        assert len(findings) > 0
        assert any("student_checker_support" in f.message and f.severity == "ERROR" for f in findings)

    def test_empty_checks_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_variables"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        checker_path = exercise_dir / "tests" / "student_checker_support.py"
        checker_path.parent.mkdir(parents=True, exist_ok=True)
        checker_path.write_text(
            "from __future__ import annotations\n"
            "from typing import Any\n"
            "CHECKS: list[Any] = []\n",
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
        metadata = {
            **_exercise_metadata(slug),
            "exercise_type": "modify",
            "parts": 1,
        }
        return _write_canonical_exercise(
            tmp_path, slug,
            metadata=metadata,
            include_explanation=False,
            missing_paths={"tests/student_checker_support.py", "tests/expectations.py"},
        )

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
# Gate H — Notebook variant overrides
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateHNotebookVariantOverrides:
    """Gate H: Verify variant overrides in student and solution notebooks."""

    def _make_notebook(self, source_lines: list[str]) -> dict:
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
            tmp_path, slug,
            metadata=metadata,
            include_explanation=False,
        )
        return exercise_dir

    def test_student_missing_variant_returns_warning(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        nb = self._make_notebook(["run_notebook_checks('ex004_sequence_modify_vars')\n"])
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(nb), encoding="utf-8")
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(nb), encoding="utf-8")
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb")
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb")

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir, student_nb=nb_student, solution_nb=nb_solution,
        )
        assert len(findings) > 0
        assert any("PYTUTOR_ACTIVE_VARIANT" in f.message for f in findings)

    def test_solution_missing_variant_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook([
            "import os\n",
            "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
            "run_notebook_checks('ex004_sequence_modify_vars')\n",
        ])
        solution_nb = self._make_notebook(["run_notebook_checks('ex004_sequence_modify_vars')\n"])
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8")
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8")
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb")
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb")

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir, student_nb=nb_student, solution_nb=nb_solution,
        )
        assert len(findings) > 0
        assert any("solution" in f.message and f.severity == "ERROR" for f in findings)

    def test_solution_wrong_variant_returns_error(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook([
            "import os\n",
            "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
            "run_notebook_checks('ex004_sequence_modify_vars')\n",
        ])
        solution_nb = self._make_notebook([
            "import os\n",
            "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
            "run_notebook_checks('ex004_sequence_modify_vars')\n",
        ])
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8")
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8")
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb")
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb")

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir, student_nb=nb_student, solution_nb=nb_solution,
        )
        assert len(findings) > 0
        assert any("instead of 'solution'" in f.message
                    and f.severity == "ERROR" for f in findings)

    def test_both_variants_correct_returns_no_finding(self, tmp_path: Path) -> None:
        slug = "ex004_sequence_modify_vars"
        exercise_dir = self._make_exercise_dir(tmp_path, slug)
        student_nb = self._make_notebook([
            "import os\n",
            "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'student'\n",
            "run_notebook_checks('ex004_sequence_modify_vars')\n",
        ])
        solution_nb = self._make_notebook([
            "import os\n",
            "os.environ['PYTUTOR_ACTIVE_VARIANT'] = 'solution'\n",
            "run_notebook_checks('ex004_sequence_modify_vars')\n",
        ])
        (exercise_dir / "notebooks" / "student.ipynb").write_text(
            json.dumps(student_nb), encoding="utf-8")
        (exercise_dir / "notebooks" / "solution.ipynb").write_text(
            json.dumps(solution_nb), encoding="utf-8")
        nb_solution = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "solution.ipynb")
        nb_student = verify_exercise_quality._load_notebook(
            exercise_dir / "notebooks" / "student.ipynb")

        findings = verify_exercise_quality._check_notebook_variant_overrides(
            ex_dir=exercise_dir, student_nb=nb_student, solution_nb=nb_solution,
        )
        assert len(findings) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Gate I — Runtime self-check
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateIRuntimeSelfCheck:
    """Gate I: Run self-checker against solution variant and report failures."""

    def test_valid_solution_returns_no_finding(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
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
            lambda key: [mock_result],
        )

        findings = verify_exercise_quality._check_runtime_self_check(
            ex_dir=exercise_dir, exercise_key=slug, nb_solution={},
        )
        assert len(findings) == 0
