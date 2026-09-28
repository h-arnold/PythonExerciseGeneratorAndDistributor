"""RED tests for the generic Classroom 50 grader and bundle builder.

These tests intentionally describe the Stage 4 command-line contract before
the two scripts exist.  They use a small fixture exercise rather than the
Selection implementation, so the future scripts cannot satisfy the contract
with Selection-specific branches.

The Stage 3 additions at the end of this module cover the four target contract
files the builder has to emit atomically once Stage 3 lands: ``requirements.txt``,
``pytest.ini``, ``classroom50_manifest.py``, and a schema-valid
``grading_manifest.json``.  The native dependency *bootstrap* itself belongs to
``tests/test_classroom50_native_bootstrap.py``, which fakes the pip subprocess so
no test in this repository reaches the network.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests._classroom50_bootstrap import (
    BUNDLE_MANIFEST_JSON_NAME,
    BUNDLE_MANIFEST_NAME,
    BUNDLE_MANIFEST_SOURCE,
    BUNDLE_PYTEST_INI_NAME,
    BUNDLE_PYTEST_INI_SOURCE,
    BUNDLE_REQUIREMENTS_NAME,
    is_manifest_records,
)
from tests._classroom50_lock import (
    REPOSITORY_PYTEST_INI,
    REQUIREMENTS_SOURCE,
    committed_requirements_bytes,
)
from tests._classroom50_test_helpers import (
    GRADING_MANIFEST_SCHEMA,
    SyntheticExercise,
    expected_row_name,
    run_bundle_child,
    write_synthetic_exercise_json,
)

RESULT_SCHEMA = "classroom50/result/v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
EXERCISE_KEY = "ex900_sequence_make_generic_fixture"
UNSELECTED_EXERCISE_KEY = "ex901_sequence_make_unselected_fixture"
CONSTRUCT = "sequence"
CASE_COUNT = 2
EXPECTED_TEST_NAMES = [
    expected_row_name(EXERCISE_KEY, "test_fixture.py::test_generic_case[alpha]"),
    expected_row_name(EXERCISE_KEY, "test_fixture.py::test_generic_case[beta]"),
]

# The four target contract files Stage 3 emits atomically into the bundle root.
TARGET_CONTRACT_FILES = (
    BUNDLE_REQUIREMENTS_NAME,
    BUNDLE_PYTEST_INI_NAME,
    BUNDLE_MANIFEST_NAME,
    BUNDLE_MANIFEST_JSON_NAME,
)
# The fixed source-to-target mapping for the three copied contract files.
COPIED_CONTRACT_SOURCES = {
    BUNDLE_REQUIREMENTS_NAME: REQUIREMENTS_SOURCE,
    BUNDLE_PYTEST_INI_NAME: BUNDLE_PYTEST_INI_SOURCE,
    BUNDLE_MANIFEST_NAME: BUNDLE_MANIFEST_SOURCE,
}


def _create_synthetic_exercise(root: Path, exercise_key: str, exercise_id: int) -> None:
    """Create one canonical exercise, including source-only unrelated assets."""
    exercise = root / "exercises" / CONSTRUCT / exercise_key
    exercise.mkdir(parents=True)
    write_synthetic_exercise_json(
        exercise,
        SyntheticExercise(
            exercise_key=exercise_key,
            exercise_id=exercise_id,
            construct=CONSTRUCT,
            title=exercise_key,
        ),
    )
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


def _run_builder(
    fixture: dict[str, Path], *, output: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the future builder's exact generic CLI contract.

    # Future CLI: --source-root is the selected exercise source tree,
    # --exercise-set is a JSON list of {construct, exercise_key} records, and
    # --runtime-source is the current runtime package source and --output is
    # the teacher-side bundle directory.  No classroom/network operation is
    # implied or permitted by this local build command.

    ``output`` overrides ``--output`` so a rejected build can be aimed at a
    second, never-populated target.
    """
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
            str(output or fixture["bundle"]),
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
    args = [
        "--student-root",
        str(fixture["student"]),
        "--result",
        str(result_path),
    ]
    if variant is not None:
        args.extend(["--variant", variant])
    return run_bundle_child(fixture["bundle"], args, cwd=REPO_ROOT)


def test_builder_copies_only_canonical_hidden_bundle_contents(
    stage4_fixture: dict[str, Path],
) -> None:
    """The builder preserves canonical paths and never copies solutions.

    Stage 3 addition: a successful build also emits the four target contract
    files at the bundle root, so the exact file set below is the Stage 2 set plus
    ``requirements.txt``, ``pytest.ini``, ``classroom50_manifest.py``, and
    ``grading_manifest.json``.
    """
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
        *(Path(name) for name in TARGET_CONTRACT_FILES),
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
    """Scores are one point per case and names omit absolute test paths.

    Stage 1 replacement: the canonical ``classroom50/result/v1`` field names
    (``schema``, per-test ``test-name`` and ``passed``) supersede the old
    ``version``/``name`` payload shape, so this assertion is red until Stage 2
    rebuilds the result document. The superseded aliases are asserted absent.
    """
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    result_path = stage4_fixture["bundle"] / "result.json"
    proc = _run_grader(stage4_fixture, result_path=result_path, variant="solution")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["schema"] == RESULT_SCHEMA
    assert "version" not in payload, "The superseded top-level 'version' alias must be gone."
    assert payload["score"] == CASE_COUNT
    assert payload["max-score"] == CASE_COUNT
    assert [item["test-name"] for item in payload["tests"]] == EXPECTED_TEST_NAMES
    assert all("name" not in item for item in payload["tests"]), "The 'name' alias must be gone."
    assert all(item["passed"] is True for item in payload["tests"])
    assert all("/" not in item["test-name"] for item in payload["tests"])
    assert all(item["score"] == item["max-score"] == 1 for item in payload["tests"])


def test_grader_forces_student_variant_and_uses_exit_zero_for_completed_failures(
    stage4_fixture: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A completed student run exits zero even when its cases fail.

    Stage 1 replacement: the row-name assertion uses the canonical
    ``test-name`` field, which supersedes the old ``name`` alias.
    """
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    monkeypatch.setenv("PYTUTOR_ACTIVE_VARIANT", "solution")
    result_path = stage4_fixture["bundle"] / "result.json"
    proc = _run_grader(stage4_fixture, result_path=result_path)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["score"] == 0
    assert payload["max-score"] == CASE_COUNT
    assert [item["test-name"] for item in payload["tests"]] == EXPECTED_TEST_NAMES
    assert [item["passed"] for item in payload["tests"]] == [False, False]
    assert [item["score"] for item in payload["tests"]] == [0, 0]
    assert [item["max-score"] for item in payload["tests"]] == [1, 1]


def test_hidden_discovery_and_sys_path_isolation_ignore_visible_tests_and_use_student_metadata(
    stage4_fixture: dict[str, Path],
) -> None:
    """Hidden tests resolve from the bundle; notebooks/metadata resolve in checkout.

    Stage 1 replacement: the tamper check reads the canonical ``test-name``
    field, which supersedes the old ``name`` alias.
    """
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
    assert all("tamper_marker" not in item["test-name"] for item in payload["tests"])


def test_template_test_tampering_does_not_change_graded_outcome(
    stage4_fixture: dict[str, Path],
) -> None:
    """Editing/deleting visible checkout tests cannot affect the hidden result.

    Stage 2 correction: the canonical payload carries ``datetime`` as the current
    UTC instant, which SPEC.md records as "current UTC time; overwritten by the
    runner with the submission instant". Two separate grading runs therefore
    differ in that one field by construction, so it cannot take part in an
    equality comparison. Every other field - including the graded rows, the
    score, and the identity - is still compared exactly.
    """
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    first = stage4_fixture["bundle"] / "first.json"
    assert _run_grader(stage4_fixture, result_path=first, variant="solution").returncode == 0
    visible_tests = stage4_fixture["student"] / "exercises" / CONSTRUCT / EXERCISE_KEY / "tests"
    shutil.rmtree(visible_tests)
    second = stage4_fixture["bundle"] / "second.json"
    assert _run_grader(stage4_fixture, result_path=second, variant="solution").returncode == 0
    first_payload = json.loads(first.read_text(encoding="utf-8"))
    second_payload = json.loads(second.read_text(encoding="utf-8"))
    del first_payload["datetime"]
    del second_payload["datetime"]
    assert first_payload == second_payload


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
    """A stale result file cannot survive an infrastructure failure.

    Stage 1 replacement: the seeded stale payload now uses the canonical
    ``classroom50/result/v1`` field names (``schema``, per-test ``test-name`` and
    ``passed``) instead of the superseded ``version``/``name`` shape. Only the
    payload shape changed; the stale-result removal contract is unchanged and
    this test stays green.
    """
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    result_path = stage4_fixture["bundle"] / "result.json"
    result_path.write_text(
        json.dumps(
            {
                "schema": RESULT_SCHEMA,
                "classroom": "local",
                "assignment": "local",
                "assignment_type": "individual",
                "owner": "local",
                "submission": "submit/local",
                "commit": "local://commit",
                "release": "local://release",
                "review": "local://review",
                "datetime": "1970-01-01T00:00:00Z",
                "score": CASE_COUNT,
                "max-score": CASE_COUNT,
                "tests": [
                    {"test-name": name, "passed": True, "score": 1, "max-score": 1}
                    for name in EXPECTED_TEST_NAMES
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


# ---------------------------------------------------------------------------
# Stage 3: the four target contract files emitted atomically by the builder.
# ---------------------------------------------------------------------------


def _read_manifest(bundle: Path) -> dict[str, Any]:
    """Return the parsed bundle grading manifest, failing with the raw text if invalid."""
    path = bundle / BUNDLE_MANIFEST_JSON_NAME
    assert path.is_file(), f"The builder must emit {BUNDLE_MANIFEST_JSON_NAME}; {path} is missing."
    parsed: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return parsed


def test_one_build_emits_the_whole_target_contract_and_a_failed_build_emits_none(
    stage4_fixture: dict[str, Path],
) -> None:
    """The four contract files are emitted together, or not at all.

    A successful build publishes the requirements, the trusted pytest
    configuration, the shared validator, and the manifest, because the autograder
    may not depend on a bundle file that a build can leave behind half-written.  The
    negative half runs against a second, never-populated target so it stays true
    whether or not a later stage also makes a failed build preserve the previous
    target's contents.
    """
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    bundle = stage4_fixture["bundle"]
    missing = [name for name in TARGET_CONTRACT_FILES if not (bundle / name).is_file()]
    assert not missing, f"The builder must emit every target contract file; missing {missing}."

    rejected = stage4_fixture["bundle"].with_name("rejected-bundle")
    stage4_fixture["exercise_set"].write_text(
        json.dumps([{"construct": CONSTRUCT, "exercise_key": "ex999_sequence_missing_tests"}]),
        encoding="utf-8",
    )
    failed = _run_builder(stage4_fixture, output=rejected)
    assert failed.returncode != 0, "A record without canonical tests must fail the build."
    leaked = [name for name in TARGET_CONTRACT_FILES if (rejected / name).exists()]
    assert not leaked, f"A failed build must not emit target contract files; found {leaked}."


@pytest.mark.parametrize(
    ("name", "source"),
    sorted(COPIED_CONTRACT_SOURCES.items()),
    ids=[name for name, _ in sorted(COPIED_CONTRACT_SOURCES.items())],
)
def test_builder_copies_each_contract_file_verbatim_from_its_committed_source(
    stage4_fixture: dict[str, Path],
    name: str,
    source: Path,
) -> None:
    """``requirements.txt``, ``pytest.ini``, and the validator are copied byte for byte.

    The autograder bootstraps from the emitted requirements file, so the bundle
    copy has to be the committed lock-derived source rather than a rewrite.
    """
    assert source.is_file(), f"{source} is not committed yet."
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    emitted = stage4_fixture["bundle"] / name
    assert emitted.read_bytes() == source.read_bytes(), (
        f"<target>/{name} must be a byte-for-byte copy of {source.name}."
    )


def test_the_committed_requirements_source_is_the_only_requirements_file(
    stage4_fixture: dict[str, Path],
) -> None:
    """The bundle ships one requirements file, and it is the committed source."""
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    bundle = stage4_fixture["bundle"]
    emitted = bundle / BUNDLE_REQUIREMENTS_NAME
    assert emitted.is_file(), f"The builder must emit {BUNDLE_REQUIREMENTS_NAME}; it is missing."
    assert emitted.read_bytes() == committed_requirements_bytes()
    assert [path.relative_to(bundle) for path in bundle.rglob("*requirements*.txt")] == [
        Path(BUNDLE_REQUIREMENTS_NAME)
    ], "The bundle must ship exactly one requirements source."


def test_the_emitted_pytest_configuration_is_not_the_repository_root_configuration(
    stage4_fixture: dict[str, Path],
) -> None:
    """The bundle gets its own minimal pytest configuration, not the root file.

    ``SPEC.md`` requires "a minimal pytest configuration separate from the
    repository's broad root ``pytest.ini``", whose ``testpaths`` would otherwise
    apply to a bundle run.
    """
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    emitted = stage4_fixture["bundle"] / BUNDLE_PYTEST_INI_NAME
    assert emitted.read_bytes() != REPOSITORY_PYTEST_INI.read_bytes(), (
        "The bundle must not reuse the repository's broad root pytest.ini."
    )


def test_builder_emits_a_schema_valid_grading_manifest_for_the_selected_records(
    stage4_fixture: dict[str, Path],
) -> None:
    """``grading_manifest.json`` is the closed wire shape for the selected records.

    Stage 3 emits the minimum closed manifest the real-builder test needs: the
    exact top-level keys, one record per selected exercise with exactly the three
    documented fields, canonical POSIX-relative paths that resolve inside the
    bundle, and records sorted by ``(construct, exercise_key)``.  Stage 5 tightens
    the canonical ``test_<exercise_key>.py`` filename rule; the fixture's
    ``test_fixture.py`` is what this stage still accepts.
    """
    build = _run_builder(stage4_fixture)
    assert build.returncode == 0, build.stderr
    bundle = stage4_fixture["bundle"]
    manifest = _read_manifest(bundle)
    assert set(manifest) == {"schema", "exercises"}, (
        f"The grading manifest has exactly two top-level keys; got {sorted(manifest)}."
    )
    assert manifest["schema"] == GRADING_MANIFEST_SCHEMA
    records = manifest["exercises"]
    assert is_manifest_records(records) and records, (
        "The manifest must list the selected records as JSON objects."
    )
    assert records == [
        {
            "construct": CONSTRUCT,
            "exercise_key": EXERCISE_KEY,
            "test_path": f"exercises/{CONSTRUCT}/{EXERCISE_KEY}/tests/test_fixture.py",
        }
    ], "One selected record must produce exactly one canonical manifest entry."
    test_path = str(records[0]["test_path"])
    assert "\\" not in test_path and ".." not in Path(test_path).parts, (
        f"{test_path!r} must be a canonical POSIX bundle-relative path."
    )
    assert (bundle / test_path).is_file(), f"{test_path!r} must resolve inside the bundle."
    assert not (bundle / "exercises" / CONSTRUCT / UNSELECTED_EXERCISE_KEY).exists(), (
        "An unselected exercise must not reach the manifest or the bundle."
    )
