"""RED tests for the generic Classroom 50 grader and bundle builder.

These tests intentionally describe the Stage 4 command-line contract before
the two scripts exist.  They use a small fixture exercise rather than the
Selection implementation, so the future scripts cannot satisfy the contract
with Selection-specific branches.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXERCISE_KEY = "ex900_sequence_make_generic_fixture"
UNSELECTED_EXERCISE_KEY = "ex901_sequence_make_unselected_fixture"
CONSTRUCT = "sequence"
CASE_COUNT = 2
EXPECTED_TEST_NAMES = [
    f"{EXERCISE_KEY}::test_fixture.py::test_generic_case[alpha]",
    f"{EXERCISE_KEY}::test_fixture.py::test_generic_case[beta]",
]


def _create_synthetic_exercise(root: Path, exercise_key: str, exercise_id: int) -> None:
    """Create one canonical exercise, including source-only unrelated assets."""
    exercise = root / "exercises" / CONSTRUCT / exercise_key
    exercise.mkdir(parents=True)
    metadata = {
        "schema_version": 1,
        "exercise_key": exercise_key,
        "exercise_id": exercise_id,
        "slug": exercise_key,
        "title": exercise_key,
        "construct": CONSTRUCT,
        "exercise_type": "make",
        "parts": 1,
    }
    (exercise / "exercise.json").write_text(json.dumps(metadata), encoding="utf-8")
    (exercise / "README.md").write_text("source-only teacher notes\n", encoding="utf-8")
    (exercise / "OVERVIEW.md").write_text("source-only overview\n", encoding="utf-8")
    (exercise / "unrelated-source-asset.txt").write_text("must not ship\n", encoding="utf-8")
    notebooks = exercise / "notebooks"
    notebooks.mkdir()
    (notebooks / "student.ipynb").write_text(
        json.dumps({"notebook_marker": "student-notebook"}), encoding="utf-8"
    )
    (notebooks / "solution.ipynb").write_text(
        json.dumps({"notebook_marker": "solution-notebook"}), encoding="utf-8"
    )


@pytest.fixture
def stage4_fixture(tmp_path: Path) -> dict[str, Path]:
    """Create source and student roots with different visible/hidden tests."""
    source_root = tmp_path / "source"
    student_root = tmp_path / "student"
    for root in (source_root, student_root):
        _create_synthetic_exercise(root, EXERCISE_KEY, 900)
        _create_synthetic_exercise(root, UNSELECTED_EXERCISE_KEY, 901)

    source_exercise = source_root / "exercises" / CONSTRUCT / EXERCISE_KEY
    student_exercise = student_root / "exercises" / CONSTRUCT / EXERCISE_KEY
    for root, marker in ((source_exercise, "bundle-hidden"), (student_exercise, "visible")):
        tests_dir = root / "tests"
        tests_dir.mkdir()
        (tests_dir / "expectations.py").write_text(f"MARKER = {marker!r}\n", encoding="utf-8")
        (tests_dir / "student_checker_support.py").write_text("CHECKS = []\n", encoding="utf-8")
        (tests_dir / "test_fixture.py").write_text(
            "import os\n"
            "import pytest\n"
            "from exercise_runtime_support.exercise_test_support import "
            "load_exercise_test_module\n"
            "from exercise_metadata.resolver import resolve_notebook_path\n\n"
            "@pytest.mark.parametrize('case', ['alpha', 'beta'])\n"
            "def test_generic_case(case):\n"
            "    assert load_exercise_test_module("
            f"{EXERCISE_KEY!r}, 'expectations').MARKER == {marker!r}\n"
            "    notebook = resolve_notebook_path("
            f"{EXERCISE_KEY!r}, 'student')\n"
            "    assert notebook.name == 'student.ipynb'\n"
            "    assert 'student-notebook' in notebook.read_text()\n"
            # The fixture deliberately passes only in the solution dry run;
            # this makes the default graded run prove both forced student
            # selection and exit-zero-for-failing-cases.
            "    assert os.environ['PYTUTOR_ACTIVE_VARIANT'] == 'solution'\n",
            encoding="utf-8",
        )

    # The metadata package is deliberately available only from the student
    # checkout.  The bundle must provide exercise_runtime_support itself.
    shutil.copytree(REPO_ROOT / "exercise_metadata", student_root / "exercise_metadata")
    runtime_source = tmp_path / "runtime-source"
    shutil.copytree(REPO_ROOT / "exercise_runtime_support", runtime_source)
    runtime_marker = runtime_source / "__init__.py"
    runtime_marker.write_text(
        runtime_marker.read_text(encoding="utf-8") + "\nBUILD_MARKER = 'first-build'\n",
        encoding="utf-8",
    )
    exercise_set = tmp_path / "exercise-set.json"
    exercise_set.write_text(
        json.dumps([{"construct": CONSTRUCT, "exercise_key": EXERCISE_KEY}]),
        encoding="utf-8",
    )
    return {
        "source": source_root,
        "student": student_root,
        "exercise_set": exercise_set,
        "runtime_source": runtime_source,
        "bundle": tmp_path / "bundle",
    }


def _run_builder(fixture: dict[str, Path]) -> subprocess.CompletedProcess[str]:
    """Run the future builder's exact generic CLI contract."""
    # Future CLI: --source-root is the selected exercise source tree,
    # --exercise-set is a JSON list of {construct, exercise_key} records, and
    # --runtime-source is the current runtime package source and --output is
    # the teacher-side bundle directory.  No classroom/network operation is
    # implied or permitted by this local build command.
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_classroom50_bundle.py"),
            "--source-root",
            str(fixture["source"]),
            "--exercise-set",
            str(fixture["exercise_set"]),
            "--runtime-source",
            str(fixture["runtime_source"]),
            "--output",
            str(fixture["bundle"]),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_grader(
    fixture: dict[str, Path], *, result_path: Path, variant: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the future bundle grader's exact local dry-run CLI contract."""
    # Future CLI: the bundle is the script root, --student-root identifies the
    # checkout whose notebooks/metadata are graded, --result writes the
    # Classroom 50 JSON, and optional --variant solution is local dry-run only.
    command = [
        sys.executable,
        str(fixture["bundle"] / "autograder.py"),
        "--student-root",
        str(fixture["student"]),
        "--result",
        str(result_path),
    ]
    if variant is not None:
        command.extend(["--variant", variant])
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def test_builder_copies_only_canonical_hidden_bundle_contents(
    stage4_fixture: dict[str, Path],
) -> None:
    """The builder preserves canonical paths and never copies solutions."""
    proc = _run_builder(stage4_fixture)
    assert proc.returncode == 0, proc.stderr
    bundle = stage4_fixture["bundle"]
    hidden = bundle / "exercises" / CONSTRUCT / EXERCISE_KEY / "tests"
    assert (bundle / "autograder.py").is_file()
    assert (hidden / "test_fixture.py").is_file()
    assert (hidden / "expectations.py").is_file()
    assert (hidden / "student_checker_support.py").is_file()
    assert (bundle / "exercise_runtime_support").is_dir()
    assert not (bundle / "exercises" / CONSTRUCT / UNSELECTED_EXERCISE_KEY).exists()
    assert not list(bundle.rglob("solution.ipynb"))
    assert not list(bundle.rglob("student.ipynb"))
    expected_files = {
        Path("autograder.py"),
        Path("exercises") / CONSTRUCT / EXERCISE_KEY / "tests" / "test_fixture.py",
        Path("exercises") / CONSTRUCT / EXERCISE_KEY / "tests" / "expectations.py",
        Path("exercises") / CONSTRUCT / EXERCISE_KEY / "tests" / "student_checker_support.py",
    }
    actual_files = {path.relative_to(bundle) for path in bundle.rglob("*") if path.is_file()}
    runtime_files = {
        path.relative_to(bundle)
        for path in (bundle / "exercise_runtime_support").rglob("*")
        if path.is_file()
    }
    assert actual_files == expected_files | runtime_files
    assert not any(
        path.name in {"README.md", "OVERVIEW.md", "unrelated-source-asset.txt"}
        for path in actual_files
    )


def test_builder_regenerates_runtime_support_from_current_source_each_build(
    stage4_fixture: dict[str, Path],
) -> None:
    """A rebuild replaces stale runtime files with the current source copy."""
    first = _run_builder(stage4_fixture)
    assert first.returncode == 0, first.stderr
    runtime_marker = stage4_fixture["runtime_source"] / "__init__.py"
    runtime_marker.write_text(
        runtime_marker.read_text(encoding="utf-8").replace(
            "BUILD_MARKER = 'first-build'", "BUILD_MARKER = 'second-build'"
        ),
        encoding="utf-8",
    )
    second = _run_builder(stage4_fixture)
    assert second.returncode == 0, second.stderr
    bundled_marker = stage4_fixture["bundle"] / "exercise_runtime_support" / "__init__.py"
    assert "BUILD_MARKER = 'second-build'" in bundled_marker.read_text(encoding="utf-8")
    assert "BUILD_MARKER = 'first-build'" not in bundled_marker.read_text(encoding="utf-8")


def test_new_scripts_accept_generic_input_without_selection_constants(
    stage4_fixture: dict[str, Path],
) -> None:
    """Neither new script hardcodes the pilot construct or exercise key."""
    proc = _run_builder(stage4_fixture)
    assert proc.returncode == 0, proc.stderr
    for script_name in ("autograder.py", "build_classroom50_bundle.py"):
        source = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert EXERCISE_KEY not in source
        assert "selection" not in source.lower()


def test_grader_result_uses_leaf_nodeids_and_documented_v1_fields(
    stage4_fixture: dict[str, Path],
) -> None:
    """Scores are one point per case and names omit absolute test paths."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    result_path = stage4_fixture["bundle"] / "result.json"
    proc = _run_grader(stage4_fixture, result_path=result_path, variant="solution")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["version"] == "classroom50/result/v1"
    assert payload["score"] == CASE_COUNT
    assert payload["max-score"] == CASE_COUNT
    assert [item["name"] for item in payload["tests"]] == EXPECTED_TEST_NAMES
    assert all("/" not in item["name"] for item in payload["tests"])
    assert all(item["score"] == item["max-score"] == 1 for item in payload["tests"])


def test_grader_forces_student_variant_and_uses_exit_zero_for_completed_failures(
    stage4_fixture: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A completed student run exits zero even when its cases fail."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")
    result_path = stage4_fixture["bundle"] / "result.json"
    proc = _run_grader(stage4_fixture, result_path=result_path)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["score"] == 0
    assert payload["max-score"] == CASE_COUNT
    assert [item["name"] for item in payload["tests"]] == EXPECTED_TEST_NAMES
    assert [item["score"] for item in payload["tests"]] == [0, 0]
    assert [item["max-score"] for item in payload["tests"]] == [1, 1]


def test_hidden_discovery_and_sys_path_isolation_ignore_visible_tests_and_use_student_metadata(
    stage4_fixture: dict[str, Path],
) -> None:
    """Hidden tests resolve from the bundle; notebooks/metadata resolve in checkout."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    visible_test = (
        stage4_fixture["student"]
        / "exercises"
        / CONSTRUCT
        / EXERCISE_KEY
        / "tests"
        / "test_fixture.py"
    )
    visible_test.write_text("def test_tamper_marker():\n    assert False\n", encoding="utf-8")
    result_path = stage4_fixture["bundle"] / "result.json"
    proc = _run_grader(stage4_fixture, result_path=result_path, variant="solution")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["max-score"] == CASE_COUNT
    assert all("tamper_marker" not in item["name"] for item in payload["tests"])


def test_template_test_tampering_does_not_change_graded_outcome(
    stage4_fixture: dict[str, Path],
) -> None:
    """Editing/deleting visible checkout tests cannot affect the hidden result."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    first = stage4_fixture["bundle"] / "first.json"
    assert _run_grader(stage4_fixture, result_path=first, variant="solution").returncode == 0
    visible_tests = stage4_fixture["student"] / "exercises" / CONSTRUCT / EXERCISE_KEY / "tests"
    shutil.rmtree(visible_tests)
    second = stage4_fixture["bundle"] / "second.json"
    assert _run_grader(stage4_fixture, result_path=second, variant="solution").returncode == 0
    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )


def test_grader_reports_infrastructure_error_for_broken_hidden_tests(
    stage4_fixture: dict[str, Path],
) -> None:
    """A collection error exits non-zero and writes no completed grade."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    hidden_test = (
        stage4_fixture["bundle"]
        / "exercises"
        / CONSTRUCT
        / EXERCISE_KEY
        / "tests"
        / "test_fixture.py"
    )
    hidden_test.write_text("def broken(:\n", encoding="utf-8")
    result_path = stage4_fixture["bundle"] / "result.json"
    proc = _run_grader(stage4_fixture, result_path=result_path, variant="solution")
    assert proc.returncode != 0
    assert not result_path.exists()


def test_grader_reports_infrastructure_error_when_no_hidden_tests_found(
    stage4_fixture: dict[str, Path],
) -> None:
    """An empty discovery set exits non-zero and writes no completed grade."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    hidden_test = (
        stage4_fixture["bundle"]
        / "exercises"
        / CONSTRUCT
        / EXERCISE_KEY
        / "tests"
        / "test_fixture.py"
    )
    hidden_test.unlink()
    result_path = stage4_fixture["bundle"] / "result.json"
    proc = _run_grader(stage4_fixture, result_path=result_path, variant="solution")
    assert proc.returncode != 0
    assert not result_path.exists()


def test_builder_copies_only_required_supports_and_excludes_unrelated_files(
    stage4_fixture: dict[str, Path],
) -> None:
    """Referenced supports ship; unreferenced, non-Python, and nested files do not."""
    source_tests = stage4_fixture["source"] / "exercises" / CONSTRUCT / EXERCISE_KEY / "tests"
    (source_tests / "extra_helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source_tests / "scratch.py").write_text("UNUSED = True\n", encoding="utf-8")
    (source_tests / "notes.txt").write_text("unrelated notes\n", encoding="utf-8")
    junk_dir = source_tests / "junk_dir"
    junk_dir.mkdir()
    (junk_dir / "junk.py").write_text("JUNK = True\n", encoding="utf-8")
    fixture_test = source_tests / "test_fixture.py"
    fixture_test.write_text(
        fixture_test.read_text(encoding="utf-8")
        + f"\nextra_helper = load_exercise_test_module({EXERCISE_KEY!r}, 'extra_helper')\n",
        encoding="utf-8",
    )
    proc = _run_builder(stage4_fixture)
    assert proc.returncode == 0, proc.stderr
    hidden = stage4_fixture["bundle"] / "exercises" / CONSTRUCT / EXERCISE_KEY / "tests"
    assert {path.name for path in hidden.iterdir() if path.is_file()} == {
        "test_fixture.py",
        "expectations.py",
        "student_checker_support.py",
        "extra_helper.py",
    }


def test_grader_removes_stale_result_before_reporting_infrastructure_error(
    stage4_fixture: dict[str, Path],
) -> None:
    """A stale result file cannot survive an infrastructure failure."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    result_path = stage4_fixture["bundle"] / "result.json"
    result_path.write_text(
        json.dumps(
            {
                "version": "classroom50/result/v1",
                "score": CASE_COUNT,
                "max-score": CASE_COUNT,
                "tests": [
                    {"name": name, "score": 1, "max-score": 1} for name in EXPECTED_TEST_NAMES
                ],
            }
        ),
        encoding="utf-8",
    )
    hidden_test = (
        stage4_fixture["bundle"]
        / "exercises"
        / CONSTRUCT
        / EXERCISE_KEY
        / "tests"
        / "test_fixture.py"
    )
    hidden_test.write_text("def broken(:\n", encoding="utf-8")
    proc = _run_grader(stage4_fixture, result_path=result_path, variant="solution")
    assert proc.returncode != 0
    assert not result_path.exists()
