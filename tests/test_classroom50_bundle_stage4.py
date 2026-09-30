"""Stage 1 tests for the generic Classroom 50 grader and bundle builder.

The bundle grader has two invocation modes.  Classroom 50 runs it with no
arguments from the student checkout and reads ``./result.json`` from there; the
local dry run passes ``--student-root``/``--result`` as a pair.  Both modes write
the canonical ``classroom50/result/v1`` document.

The synthetic fixture exercises keep the contract independent of any
construct-specific grader branch, and every Classroom 50 mode run injects an
offline ``pip`` test double, so the install boundary is observable without a
real install or network access.  One real exercise set is built and graded to
confirm the generic builder/grader cycle end to end.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "classroom50/result/v1"
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
# The fields that carry the grade. Identity and the wall-clock `datetime` are
# deliberately excluded, so comparing two results asserts the grade rather than
# the moment the grade happened to be taken.
GRADE_BEARING_FIELDS = ("schema", "score", "max-score", "tests")

EXERCISE_KEY = "ex900_sequence_make_generic_fixture"
UNSELECTED_EXERCISE_KEY = "ex901_sequence_make_unselected_fixture"
CONSTRUCT = "sequence"
CASE_COUNT = 2
EXPECTED_TEST_NAMES = [
    f"{EXERCISE_KEY}::test_fixture.py::test_generic_case[alpha]",
    f"{EXERCISE_KEY}::test_fixture.py::test_generic_case[beta]",
]

CLASSROOM50_EXERCISE_KEY = "ex902_sequence_make_classroom50_fixture"
CLASSROOM50_CASE_COUNT = 3
HIDDEN_COPY_CASE = (
    f"{CLASSROOM50_EXERCISE_KEY}::test_fixture.py::test_hidden_copy_is_graded_with_student_variant"
)
SOLUTION_ONLY_CASE = f"{CLASSROOM50_EXERCISE_KEY}::test_fixture.py::test_solution_dry_run_only_case"
TEARDOWN_CASE = f"{CLASSROOM50_EXERCISE_KEY}::test_teardown.py::test_call_passes_but_teardown_fails"
CLASSROOM50_CASE_NAMES = [HIDDEN_COPY_CASE, SOLUTION_ONLY_CASE, TEARDOWN_CASE]

REAL_CONSTRUCT = "sequence"
REAL_EXERCISE_KEY = "ex002_sequence_modify_basics"

COMMIT_URL = "https://example.invalid/commit/abc123"
RELEASE_URL = "https://example.invalid/release/1"
REVIEW_URL = "https://example.invalid/review/1"
RUNNER_IDENTITY = {
    "CLASSROOM": "intro-python",
    "ASSIGNMENT": "sequence-pilot",
    "ASSIGNMENT_TYPE": "individual",
    "SUBMISSION_TAG": "submit/0001",
    "COMMIT_URL": COMMIT_URL,
    "RELEASE_URL": RELEASE_URL,
    "OWNER": "octocat",
    "USERNAME": "username-fallback",
    "REVIEW_URL": REVIEW_URL,
}
REQUIRED_ENVIRONMENT_VARIABLES = (
    "CLASSROOM",
    "ASSIGNMENT",
    "ASSIGNMENT_TYPE",
    "SUBMISSION_TAG",
    "COMMIT_URL",
    "RELEASE_URL",
)
# OWNER is required too, but USERNAME satisfies it, so a run missing only OWNER
# must still succeed; only losing both can fail.
FALLBACK_IDENTITY_VARIABLES = ("OWNER", "USERNAME")
# Every runner variable is cleared before a test builds its own environment, so a
# developer's shell cannot leak identity into a mode that must not see it.
RUNNER_VARIABLES = (*REQUIRED_ENVIRONMENT_VARIABLES, *FALLBACK_IDENTITY_VARIABLES, "REVIEW_URL")
UNRELATED_RUNNER_VARIABLES = {
    "GITHUB_ACTOR": "unrelated-runner-actor",
    "RUNNER_TEMP": "/tmp/unrelated-runner",
}

_PIP_DOUBLE_LOG_ENV = "CLASSROOM50_TEST_PIP_LOG"
_PIP_DOUBLE_FAIL_ENV = "CLASSROOM50_TEST_PIP_FAIL"

_SITECUSTOMIZE_SOURCE = '''\
"""Record the first pytest import of the grading interpreter."""
import json
import os
import sys


class _PytestImportRecorder:
    """Append one event the first time pytest is imported."""

    def find_spec(self, fullname, path=None, target=None):
        log = os.environ.get("__LOG_ENV__")
        if fullname == "pytest" and log:
            with open(log, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event": "import", "module": fullname}) + "\\n")
        return None


sys.meta_path.insert(0, _PytestImportRecorder())
'''

_PIP_DOUBLE_MAIN_SOURCE = '''\
"""Offline pip test double: records the request and never reaches the network."""
import json
import os
import sys

log = os.environ.get("__LOG_ENV__")
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "pip", "argv": sys.argv[1:]}) + "\\n")
sys.exit(1 if os.environ.get("__FAIL_ENV__") else 0)
'''


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


def _write_classroom50_hidden_tests(source_tests: Path, student_tests: Path) -> None:
    """Write the hidden and visible test copies used by the two-mode fixture.

    The hidden copy asserts the bundle-only marker, the forced student variant,
    and student-checkout notebook resolution, so it passes in both modes.  The
    solution-only case passes only in the local dry run, and the teardown module
    passes its call phase while failing teardown.
    """
    for tests_dir, marker in ((source_tests, "bundle-hidden"), (student_tests, "visible")):
        tests_dir.mkdir(parents=True)
        (tests_dir / "expectations.py").write_text(f"MARKER = {marker!r}\n", encoding="utf-8")
        (tests_dir / "student_checker_support.py").write_text("CHECKS = []\n", encoding="utf-8")
    (source_tests / "test_fixture.py").write_text(
        "import os\n"
        "from exercise_metadata.resolver import resolve_notebook_path\n"
        "from exercise_runtime_support.exercise_test_support import "
        "load_exercise_test_module\n\n"
        "EXERCISE_KEY = "
        f"{CLASSROOM50_EXERCISE_KEY!r}\n\n\n"
        "def test_hidden_copy_is_graded_with_student_variant():\n"
        "    assert os.environ['PYTUTOR_ACTIVE_VARIANT'] == 'student'\n"
        "    assert load_exercise_test_module("
        "EXERCISE_KEY, 'expectations').MARKER == 'bundle-hidden'\n"
        "    notebook = resolve_notebook_path(EXERCISE_KEY, 'student')\n"
        "    assert 'student-notebook' in notebook.read_text()\n\n\n"
        "def test_solution_dry_run_only_case():\n"
        "    assert os.environ['PYTUTOR_ACTIVE_VARIANT'] == 'solution'\n",
        encoding="utf-8",
    )
    (source_tests / "test_teardown.py").write_text(
        "import pytest\n\n\n"
        "@pytest.fixture\n"
        "def failing_teardown():\n"
        "    yield\n"
        "    raise AssertionError('teardown phase failed')\n\n\n"
        "def test_call_passes_but_teardown_fails(failing_teardown):\n"
        "    assert True\n",
        encoding="utf-8",
    )
    (student_tests / "test_fixture.py").write_text(
        "def test_visible_copy_must_not_be_graded():\n    assert False\n", encoding="utf-8"
    )


@pytest.fixture
def classroom50_fixture(tmp_path: Path) -> dict[str, Path]:
    """Create a source tree, student checkout, and a separately extracted bundle."""
    source_root = tmp_path / "source"
    student_root = tmp_path / "student"
    for root in (source_root, student_root):
        _create_synthetic_exercise(root, CLASSROOM50_EXERCISE_KEY, 902)

    source_tests = source_root / "exercises" / CONSTRUCT / CLASSROOM50_EXERCISE_KEY / "tests"
    student_tests = student_root / "exercises" / CONSTRUCT / CLASSROOM50_EXERCISE_KEY / "tests"
    _write_classroom50_hidden_tests(source_tests, student_tests)

    # exercise_metadata ships only with the student checkout, so grading proves
    # the checkout is the student root.
    shutil.copytree(REPO_ROOT / "exercise_metadata", student_root / "exercise_metadata")
    runtime_source = tmp_path / "runtime-source"
    shutil.copytree(REPO_ROOT / "exercise_runtime_support", runtime_source)
    exercise_set = tmp_path / "exercise-set.json"
    exercise_set.write_text(
        json.dumps([{"construct": CONSTRUCT, "exercise_key": CLASSROOM50_EXERCISE_KEY}]),
        encoding="utf-8",
    )
    return {
        "source": source_root,
        "student": student_root,
        "exercise_set": exercise_set,
        "runtime_source": runtime_source,
        "bundle": tmp_path / "bundle",
        # Classroom 50 extracts the bundle beside the checkout, not inside it.
        "extracted_bundle": tmp_path / "classroom50-extract" / "assignment" / "bundle",
    }


@dataclass(frozen=True)
class _PipDouble:
    """An offline ``pip`` test double injected through ``PYTHONPATH``.

    The double intercepts ``sys.executable -m pip`` and appends its request to a
    shared log.  A ``sitecustomize`` meta-path hook appends the first
    ``import pytest`` of the grading interpreter to the same log.  The grader
    waits for the install to finish, so the log order is the real install and
    import order.
    """

    pythonpath: Path
    log: Path

    @property
    def events(self) -> list[dict[str, Any]]:
        """Return the recorded install/import events in the order they happened."""
        if not self.log.is_file():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    @property
    def install_requests(self) -> list[list[str]]:
        """Return the argv of every recorded pip request."""
        return [event["argv"] for event in self.events if event["event"] == "pip"]

    @property
    def recorded_kinds(self) -> list[str]:
        """Return the recorded event names in order, ignoring the payloads."""
        return [event["event"] for event in self.events]


@pytest.fixture
def pip_double(tmp_path: Path) -> _PipDouble:
    """Create the offline pip double for one test."""
    pythonpath = tmp_path / "pip-double"
    (pythonpath / "pip").mkdir(parents=True)
    (pythonpath / "pip" / "__init__.py").write_text(
        '"""Offline pip test double."""\n', encoding="utf-8"
    )
    (pythonpath / "pip" / "__main__.py").write_text(
        _PIP_DOUBLE_MAIN_SOURCE.replace("__LOG_ENV__", _PIP_DOUBLE_LOG_ENV).replace(
            "__FAIL_ENV__", _PIP_DOUBLE_FAIL_ENV
        ),
        encoding="utf-8",
    )
    (pythonpath / "sitecustomize.py").write_text(
        _SITECUSTOMIZE_SOURCE.replace("__LOG_ENV__", _PIP_DOUBLE_LOG_ENV), encoding="utf-8"
    )
    return _PipDouble(pythonpath=pythonpath, log=tmp_path / "pip-events.jsonl")


def _base_environment() -> dict[str, str]:
    """Return the current environment without any Classroom 50 identity."""
    environment = dict(os.environ)
    for name in RUNNER_VARIABLES:
        environment.pop(name, None)
    environment.pop("PYTUTOR_ACTIVE_VARIANT", None)
    return environment


def _with_pip_double(
    environment: dict[str, str], double: _PipDouble, *, fail: bool = False
) -> dict[str, str]:
    """Return ``environment`` with the pip double first on ``PYTHONPATH``.

    The pip environment settings are a guard: should a future implementation
    ever bypass the double, a real pip must fail offline instead of reaching the
    network from a repository test.
    """
    result = dict(environment)
    existing = result.get("PYTHONPATH")
    result["PYTHONPATH"] = str(double.pythonpath) + (os.pathsep + existing if existing else "")
    result[_PIP_DOUBLE_LOG_ENV] = str(double.log)
    if fail:
        result[_PIP_DOUBLE_FAIL_ENV] = "1"
    result["PIP_NO_INDEX"] = "1"
    result["PIP_RETRIES"] = "0"
    result["PIP_TIMEOUT"] = "1"
    result["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return result


def _classroom_environment(double: _PipDouble, **changes: str | None) -> dict[str, str]:
    """Return a Classroom 50 runner environment, with unrelated variables present.

    ``changes`` sets the named variable, or removes it when the value is ``None``.
    """
    environment = _with_pip_double(_base_environment(), double)
    environment.update(RUNNER_IDENTITY)
    environment.update(UNRELATED_RUNNER_VARIABLES)
    for name, value in changes.items():
        if value is None:
            environment.pop(name, None)
        else:
            environment[name] = value
    return environment


def _build_bundle(
    *, source_root: Path, exercise_set: Path, runtime_source: Path, output: Path
) -> subprocess.CompletedProcess[str]:
    """Run the builder's exact generic CLI contract."""
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_classroom50_bundle.py"),
            "--source-root",
            str(source_root),
            "--exercise-set",
            str(exercise_set),
            "--runtime-source",
            str(runtime_source),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_builder(fixture: dict[str, Path]) -> subprocess.CompletedProcess[str]:
    """Build the fixture's bundle from its source tree."""
    return _build_bundle(
        source_root=fixture["source"],
        exercise_set=fixture["exercise_set"],
        runtime_source=fixture["runtime_source"],
        output=fixture["bundle"],
    )


def _run_grader_argv(
    bundle: Path,
    arguments: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke a bundle's grader copy with an explicit argument list."""
    return subprocess.run(
        [sys.executable, str(bundle / "autograder.py"), *arguments],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_grader(
    fixture: dict[str, Path],
    *,
    result_path: Path,
    variant: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the bundle grader's exact local dry-run CLI contract."""
    arguments = [
        "--student-root",
        str(fixture["student"]),
        "--result",
        str(result_path),
    ]
    if variant is not None:
        arguments.extend(["--variant", variant])
    return _run_grader_argv(fixture["bundle"], arguments, cwd=REPO_ROOT, env=env)


def _run_classroom50_grader(
    fixture: dict[str, Path],
    double: _PipDouble,
    *,
    changes: dict[str, str | None] | None = None,
    bundle: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the bundle grader with no arguments from the student checkout."""
    return _run_grader_argv(
        bundle or fixture["bundle"],
        [],
        cwd=fixture["student"],
        env=_classroom_environment(double, **(changes or {})),
    )


def _classroom50_result(fixture: dict[str, Path]) -> Path:
    """Return the documented Classroom 50 result path inside the checkout."""
    return fixture["student"] / "result.json"


def _read_result(path: Path) -> dict[str, Any]:
    """Read a written result document, failing fast when it is absent."""
    assert path.is_file(), f"no result document was written at {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _case_names(payload: dict[str, Any]) -> list[str]:
    """Return the canonical case names of a result document, in result order."""
    return [row["test-name"] for row in payload["tests"]]


def _case_scores(payload: dict[str, Any]) -> dict[str, int]:
    """Map each canonical case name to its awarded score."""
    return {row["test-name"]: row["score"] for row in payload["tests"]}


def _grade_bearing_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Return only the fields of a result document that carry the grade.

    ``datetime`` is a one-second wall-clock stamp, so including it would make
    two runs of the same bundle compare unequal whenever they straddle a second
    boundary.  The identity fields are excluded for the same reason
    ``_assert_canonical_result_shape`` never pins an exact key set: Classroom
    50 re-stamps them, so they say nothing about the grade.
    """
    return {field: payload[field] for field in GRADE_BEARING_FIELDS}


def _assert_canonical_result_shape(payload: dict[str, Any]) -> None:
    """Assert the canonical result envelope and per-case row fields.

    Only two things are pinned: the canonical keys are present with the right
    values, and the superseded aliases are gone.  The checks are deliberately
    subset and absence checks, never exact key sets, because Classroom 50's
    runner re-stamps fields such as ``graded_at`` and ``submitted_by`` and a
    future valid field must not fail this helper.
    """
    assert payload["schema"] == SCHEMA, "the canonical 'schema' field must carry the version"
    assert "version" not in payload, "the superseded 'version' field must be removed"
    for row in payload["tests"]:
        assert "name" not in row, "the superseded 'name' field must be removed"
        assert {"test-name", "passed", "score", "max-score"} <= set(row), (
            f"case row must use the canonical field names, got {sorted(row)}"
        )
        assert row["max-score"] == 1, "one point per case is the only weighting"
        assert row["passed"] is (row["score"] == 1), (
            "'passed' must agree with the awarded score for every case"
        )


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
        assert CLASSROOM50_EXERCISE_KEY not in source
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
    payload = _read_result(result_path)
    _assert_canonical_result_shape(payload)
    assert payload["score"] == CASE_COUNT
    assert payload["max-score"] == CASE_COUNT
    assert _case_names(payload) == EXPECTED_TEST_NAMES
    assert all("/" not in name for name in _case_names(payload))
    assert all(row["score"] == row["max-score"] == 1 for row in payload["tests"])


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
    payload = _read_result(result_path)
    assert payload["score"] == 0
    assert payload["max-score"] == CASE_COUNT
    assert _case_names(payload) == EXPECTED_TEST_NAMES
    assert _case_scores(payload) == dict.fromkeys(EXPECTED_TEST_NAMES, 0)
    assert [row["passed"] for row in payload["tests"]] == [False, False]
    assert [row["max-score"] for row in payload["tests"]] == [1, 1]


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
    payload = _read_result(result_path)
    assert payload["max-score"] == CASE_COUNT
    assert all("tamper_marker" not in name for name in _case_names(payload))


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
    assert _grade_bearing_fields(_read_result(first)) == _grade_bearing_fields(_read_result(second))


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
                "schema": SCHEMA,
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


def test_classroom50_mode_roots_checkout_at_cwd_and_bundle_at_script_parent(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """A no-argument run grades cwd, collects from the script's bundle, writes ./result.json."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    extracted = classroom50_fixture["extracted_bundle"]
    shutil.copytree(classroom50_fixture["bundle"], extracted)

    proc = _run_classroom50_grader(classroom50_fixture, pip_double, bundle=extracted)

    assert proc.returncode == 0, proc.stderr
    assert not (extracted / "result.json").exists(), (
        "the result belongs to the student checkout, not the bundle"
    )
    assert not (classroom50_fixture["bundle"] / "result.json").exists()
    payload = _read_result(_classroom50_result(classroom50_fixture))
    assert _case_names(payload) == CLASSROOM50_CASE_NAMES
    assert payload["max-score"] == CLASSROOM50_CASE_COUNT
    # Only the bundle-only case passes: the visible checkout copy is never
    # collected, and the forced student variant is observed by the runtime.
    assert _case_scores(payload) == {HIDDEN_COPY_CASE: 1, SOLUTION_ONLY_CASE: 0, TEARDOWN_CASE: 0}
    _assert_canonical_result_shape(payload)


def test_classroom50_mode_reads_identity_from_documented_environment(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """Every identity field of the result comes from the documented runner variables."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(classroom50_fixture, pip_double)

    assert proc.returncode == 0, proc.stderr
    payload = _read_result(_classroom50_result(classroom50_fixture))
    assert payload["classroom"] == RUNNER_IDENTITY["CLASSROOM"]
    assert payload["assignment"] == RUNNER_IDENTITY["ASSIGNMENT"]
    assert payload["assignment_type"] == RUNNER_IDENTITY["ASSIGNMENT_TYPE"]
    assert payload["owner"] == RUNNER_IDENTITY["OWNER"]
    assert payload["submission"] == RUNNER_IDENTITY["SUBMISSION_TAG"]
    assert payload["commit"] == COMMIT_URL
    assert payload["release"] == RELEASE_URL
    assert payload["review"] == REVIEW_URL
    assert DATETIME_PATTERN.match(payload["datetime"]), (
        "datetime must use the documented YYYY-MM-DDTHH:MM:SSZ shape"
    )
    assert payload["score"] == sum(row["score"] for row in payload["tests"])
    assert payload["max-score"] == len(payload["tests"])
    _assert_canonical_result_shape(payload)


def test_classroom50_mode_owner_falls_back_to_username(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """A run missing only OWNER still succeeds, using USERNAME as its fallback."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(classroom50_fixture, pip_double, changes={"OWNER": None})

    assert proc.returncode == 0, proc.stderr
    payload = _read_result(_classroom50_result(classroom50_fixture))
    assert payload["owner"] == RUNNER_IDENTITY["USERNAME"]


def test_classroom50_mode_missing_owner_and_username_writes_no_result(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """Losing both identity variables is a grading failure, not a vacuous pass."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(
        classroom50_fixture, pip_double, changes={"OWNER": None, "USERNAME": None}
    )

    assert proc.returncode != 0, "a run with no owner identity must exit non-zero"
    assert not _classroom50_result(classroom50_fixture).exists()
    assert re.search(r"owner|username", proc.stderr, re.IGNORECASE), (
        "the failure must name the missing identity variable"
    )


@pytest.mark.parametrize(
    ("review_url", "expected_review"),
    [
        pytest.param(None, COMMIT_URL, id="falls-back-to-commit-url"),
        pytest.param(
            "https://example.invalid/review/9", "https://example.invalid/review/9", id="explicit"
        ),
    ],
)
def test_classroom50_mode_review_url_falls_back_to_commit_url(
    classroom50_fixture: dict[str, Path],
    pip_double: _PipDouble,
    review_url: str | None,
    expected_review: str,
) -> None:
    """REVIEW_URL is optional and defaults to COMMIT_URL."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(
        classroom50_fixture, pip_double, changes={"REVIEW_URL": review_url}
    )

    assert proc.returncode == 0, proc.stderr
    payload = _read_result(_classroom50_result(classroom50_fixture))
    assert payload["review"] == expected_review
    assert payload["commit"] == COMMIT_URL


@pytest.mark.parametrize("assignment_type", ["individual", "group", "team"])
def test_classroom50_mode_supports_every_documented_assignment_type(
    classroom50_fixture: dict[str, Path],
    pip_double: _PipDouble,
    assignment_type: str,
) -> None:
    """individual, group, and team are accepted and echoed into the result."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(
        classroom50_fixture, pip_double, changes={"ASSIGNMENT_TYPE": assignment_type}
    )

    assert proc.returncode == 0, proc.stderr
    payload = _read_result(_classroom50_result(classroom50_fixture))
    assert payload["assignment_type"] == assignment_type


@pytest.mark.parametrize("variable", REQUIRED_ENVIRONMENT_VARIABLES)
def test_classroom50_mode_missing_required_environment_writes_no_result(
    classroom50_fixture: dict[str, Path],
    pip_double: _PipDouble,
    variable: str,
) -> None:
    """A missing required runner variable fails clearly and grades nothing."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(classroom50_fixture, pip_double, changes={variable: None})

    assert proc.returncode != 0, "a run that cannot grade must exit non-zero"
    assert not _classroom50_result(classroom50_fixture).exists()
    assert variable.lower() in proc.stderr.lower(), (
        f"the failure must name the missing {variable} value"
    )


@pytest.mark.parametrize("assignment_type", ["solo", "plenary", ""])
def test_classroom50_mode_rejects_unsupported_assignment_type(
    classroom50_fixture: dict[str, Path],
    pip_double: _PipDouble,
    assignment_type: str,
) -> None:
    """An unsupported assignment type is a grading failure, not a vacuous pass."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(
        classroom50_fixture, pip_double, changes={"ASSIGNMENT_TYPE": assignment_type}
    )

    assert proc.returncode != 0, "an unsupported assignment type must exit non-zero"
    assert not _classroom50_result(classroom50_fixture).exists()
    assert re.search(r"assignment[ _]type", proc.stderr, re.IGNORECASE), (
        "the failure must name the unsupported assignment type"
    )


def test_classroom50_mode_forces_student_variant_over_a_preset_environment(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """The graded run forces the student variant, whatever the environment carries."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(
        classroom50_fixture, pip_double, changes={"PYTUTOR_ACTIVE_VARIANT": "solution"}
    )

    assert proc.returncode == 0, proc.stderr
    scores = _case_scores(_read_result(_classroom50_result(classroom50_fixture)))
    assert scores[HIDDEN_COPY_CASE] == 1, "the student-variant case must be the graded one"
    assert scores[SOLUTION_ONLY_CASE] == 0, "the solution variant must not be graded"


def test_teardown_failure_never_scores_a_point(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """A case whose call phase passes but whose teardown fails cannot score.

    In the solution dry run only the solution-variant case scores, so the score
    must be one even though the teardown case's call phase passed.  The sums are
    used deliberately: they are the scoring surface, independent of the result
    field names.
    """
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    result_path = classroom50_fixture["bundle"] / "teardown-result.json"

    proc = _run_grader(
        classroom50_fixture,
        result_path=result_path,
        variant="solution",
        env=_with_pip_double(_base_environment(), pip_double),
    )

    assert proc.returncode == 0, proc.stderr
    payload = _read_result(result_path)
    assert payload["max-score"] == CLASSROOM50_CASE_COUNT
    assert payload["score"] == 1, (
        "a teardown failure is a real failure of that case, so it cannot score"
    )


def test_classroom50_mode_does_not_grade_the_visible_checkout_copy(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """Collection is rooted in the bundle, never in the checkout's visible copies."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    visible = (
        classroom50_fixture["student"]
        / "exercises"
        / CONSTRUCT
        / CLASSROOM50_EXERCISE_KEY
        / "tests"
    )
    shutil.rmtree(visible)

    proc = _run_classroom50_grader(classroom50_fixture, pip_double)

    assert proc.returncode == 0, proc.stderr
    payload = _read_result(_classroom50_result(classroom50_fixture))
    assert _case_names(payload) == CLASSROOM50_CASE_NAMES
    assert payload["max-score"] == CLASSROOM50_CASE_COUNT


@pytest.mark.parametrize("failure", ["missing-environment", "broken-hidden-tests"])
def test_classroom50_mode_removes_a_stale_checkout_result_before_grading(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble, failure: str
) -> None:
    """A stale ./result.json can never survive a run that cannot grade."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    result_path = _classroom50_result(classroom50_fixture)
    result_path.write_text(
        json.dumps(
            {
                "schema": SCHEMA,
                "score": CLASSROOM50_CASE_COUNT,
                "max-score": CLASSROOM50_CASE_COUNT,
                "tests": [
                    {"test-name": name, "passed": True, "score": 1, "max-score": 1}
                    for name in CLASSROOM50_CASE_NAMES
                ],
            }
        ),
        encoding="utf-8",
    )
    changes: dict[str, str | None] = (
        {"ASSIGNMENT": None} if failure == "missing-environment" else {}
    )
    if failure == "broken-hidden-tests":
        (
            classroom50_fixture["bundle"]
            / "exercises"
            / CONSTRUCT
            / CLASSROOM50_EXERCISE_KEY
            / "tests"
            / "test_fixture.py"
        ).write_text("def broken(:\n", encoding="utf-8")

    proc = _run_classroom50_grader(classroom50_fixture, pip_double, changes=changes)

    assert proc.returncode != 0
    assert not result_path.exists(), "the stale grade must be removed before grading"


def test_classroom50_mode_installs_test_dependencies_before_importing_pytest(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """The grading interpreter installs pytest and tabulate, then imports pytest."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr

    proc = _run_classroom50_grader(classroom50_fixture, pip_double)

    assert proc.returncode == 0, proc.stderr
    # The pip entry is written by the install subprocess and the import entry by
    # the grading interpreter itself, so the recorded order is the real order.
    kinds = pip_double.recorded_kinds
    assert "pip" in kinds, (
        f"the grading interpreter must install its dependencies, recorded: {kinds}"
    )
    assert "import" in kinds, f"the grader must import pytest, recorded: {kinds}"
    assert kinds.index("import") > kinds.index("pip"), (
        f"pytest must be imported only after the install, recorded events: {kinds}"
    )
    installs = pip_double.install_requests
    assert any("install" in argv for argv in installs), (
        f"the double must be called with an install request, got {installs}"
    )
    # The dependency set is checked across the recorded requests, not inside a
    # single call, so a grader may install in more than one step.
    requested = {token for argv in installs for token in argv}
    # pytest runs the bundle and tabulate is imported by the runtime reporting
    # module, so both are part of the grading dependency set.
    assert {"pytest", "tabulate"} <= requested, (
        f"both grading dependencies must be installed, got {installs}"
    )
    assert _read_result(_classroom50_result(classroom50_fixture))["schema"] == SCHEMA


def test_classroom50_mode_fails_without_a_result_when_the_install_fails(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """A failed dependency install is an infrastructure error, not a grade."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    failing = _with_pip_double(_base_environment(), pip_double, fail=True)

    proc = _run_grader_argv(
        classroom50_fixture["bundle"],
        [],
        cwd=classroom50_fixture["student"],
        env=failing,
    )

    assert pip_double.install_requests, "the failing install must have been attempted"
    assert proc.returncode != 0, "a failed install must exit non-zero"
    assert not _classroom50_result(classroom50_fixture).exists()


def test_local_mode_never_installs_dependencies(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """The local dry run uses the developer's environment, so a failing pip is irrelevant."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    result_path = classroom50_fixture["bundle"] / "local-result.json"

    proc = _run_grader(
        classroom50_fixture,
        result_path=result_path,
        variant="solution",
        env=_with_pip_double(_base_environment(), pip_double, fail=True),
    )

    assert proc.returncode == 0, proc.stderr
    assert pip_double.install_requests == [], "local mode must not run a pip install"
    # The recorder must have seen this interpreter, so the check above is not vacuous.
    assert "import" in pip_double.recorded_kinds, (
        f"the recorder must observe the local grading run, recorded: {pip_double.recorded_kinds}"
    )
    assert _read_result(result_path)["schema"] == SCHEMA


@pytest.mark.parametrize("runner_environment", [False, True], ids=["no-env", "runner-env"])
def test_local_mode_emits_documented_non_uploadable_identity(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble, runner_environment: bool
) -> None:
    """Local results carry the documented local identity and need no runner environment.

    The dry run is graded the same way with and without Classroom 50 variables
    present, so a local result can never be mistaken for collected identity.
    """
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    result_path = classroom50_fixture["bundle"] / "local-result.json"
    environment = (
        _classroom_environment(pip_double)
        if runner_environment
        else _with_pip_double(_base_environment(), pip_double)
    )

    proc = _run_grader(
        classroom50_fixture,
        result_path=result_path,
        variant="solution",
        env=environment,
    )

    assert proc.returncode == 0, proc.stderr
    payload = _read_result(result_path)
    assert payload["classroom"] == "local"
    assert payload["assignment"] == "local"
    assert payload["assignment_type"] == "individual"
    assert payload["owner"] == "local"
    assert payload["submission"] == "submit/local"
    assert payload["commit"].startswith("local://")
    assert payload["release"].startswith("local://")
    assert payload["review"].startswith("local://")
    assert DATETIME_PATTERN.match(payload["datetime"])
    _assert_canonical_result_shape(payload)


def test_local_mode_solution_dry_run_selects_the_solution_variant(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """--variant solution reaches the runtime, and the teardown case still fails."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    result_path = classroom50_fixture["bundle"] / "local-result.json"

    proc = _run_grader(
        classroom50_fixture,
        result_path=result_path,
        variant="solution",
        env=_with_pip_double(_base_environment(), pip_double),
    )

    assert proc.returncode == 0, proc.stderr
    scores = _case_scores(_read_result(result_path))
    assert scores[SOLUTION_ONLY_CASE] == 1, "--variant solution must expose the solution notebooks"
    assert scores[HIDDEN_COPY_CASE] == 0, "a student-only case still fails on the solution variant"
    assert scores[TEARDOWN_CASE] == 0


def test_both_invocation_modes_report_the_same_case_names_and_maxima(
    classroom50_fixture: dict[str, Path], pip_double: _PipDouble
) -> None:
    """The two modes grade the same bundle, so their case names and maxima agree."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    local_result = classroom50_fixture["bundle"] / "local-result.json"

    local = _run_grader(
        classroom50_fixture,
        result_path=local_result,
        variant="solution",
        env=_with_pip_double(_base_environment(), pip_double),
    )
    assert local.returncode == 0, local.stderr
    classroom50 = _run_classroom50_grader(classroom50_fixture, pip_double)
    assert classroom50.returncode == 0, classroom50.stderr

    local_payload = _read_result(local_result)
    runner_payload = _read_result(_classroom50_result(classroom50_fixture))
    assert _case_names(runner_payload) == _case_names(local_payload) == CLASSROOM50_CASE_NAMES
    assert runner_payload["max-score"] == local_payload["max-score"] == CLASSROOM50_CASE_COUNT
    assert all(
        name.startswith(f"{CLASSROOM50_EXERCISE_KEY}::") for name in _case_names(local_payload)
    )
    assert all("/" not in name for name in _case_names(runner_payload))


@pytest.mark.parametrize("option", ["--student-root", "--result"])
def test_a_single_local_option_is_a_usage_error(
    classroom50_fixture: dict[str, Path], option: str
) -> None:
    """--student-root and --result are required as a pair, so one alone is a usage error."""
    build = _run_builder(classroom50_fixture)
    assert build.returncode == 0, build.stderr
    requested_result = classroom50_fixture["bundle"] / "unused-result.json"
    value = (
        str(classroom50_fixture["student"]) if option == "--student-root" else str(requested_result)
    )

    proc = _run_grader_argv(classroom50_fixture["bundle"], [option, value], cwd=REPO_ROOT)

    assert proc.returncode != 0, f"{option} alone must be rejected"
    assert proc.stderr.strip(), "a usage error must explain itself"
    assert not requested_result.exists(), "a usage error must write no result"
    assert not _classroom50_result(classroom50_fixture).exists()


def test_real_exercise_set_builds_and_grades_in_both_variants(
    tmp_path: Path, pip_double: _PipDouble
) -> None:
    """A real exercise set builds offline and grades full-pass on the solution variant."""
    exercise_set = tmp_path / "real-exercise-set.json"
    exercise_set.write_text(
        json.dumps([{"construct": REAL_CONSTRUCT, "exercise_key": REAL_EXERCISE_KEY}]),
        encoding="utf-8",
    )
    bundle = tmp_path / "real-bundle"

    build = _build_bundle(
        source_root=REPO_ROOT,
        exercise_set=exercise_set,
        runtime_source=REPO_ROOT / "exercise_runtime_support",
        output=bundle,
    )

    assert build.returncode == 0, build.stderr
    assert (bundle / "autograder.py").is_file()
    assert (bundle / "exercise_runtime_support").is_dir()
    hidden = bundle / "exercises" / REAL_CONSTRUCT / REAL_EXERCISE_KEY / "tests"
    assert list(hidden.glob("test_*.py")), "the selected hidden tests must be bundled"
    assert not list(bundle.rglob("*.ipynb")), "notebooks must never enter a bundle"
    assert not list(bundle.rglob("exercise.json")), "exercise metadata must never enter a bundle"
    assert not (bundle / "exercises" / REAL_CONSTRUCT / REAL_EXERCISE_KEY / "notebooks").exists(), (
        "the canonical source notebooks stay out of the bundle"
    )

    solution_result = tmp_path / "real-solution.json"
    solution = _run_grader_argv(
        bundle,
        [
            "--student-root",
            str(REPO_ROOT),
            "--result",
            str(solution_result),
            "--variant",
            "solution",
        ],
        cwd=tmp_path,
        env=_with_pip_double(_base_environment(), pip_double),
    )
    assert solution.returncode == 0, solution.stderr
    solution_payload = _read_result(solution_result)
    assert solution_payload["max-score"] >= 1
    assert solution_payload["score"] == solution_payload["max-score"], (
        "the solution dry run must confirm a full pass"
    )
    assert all(name.startswith(f"{REAL_EXERCISE_KEY}::") for name in _case_names(solution_payload))
    assert all("/" not in name for name in _case_names(solution_payload))

    # The student variant is the classroom surface: expected failures, exit zero,
    # and the same case names and maxima as the solution dry run.
    student_result = tmp_path / "real-student.json"
    student = _run_grader_argv(
        bundle,
        ["--student-root", str(REPO_ROOT), "--result", str(student_result)],
        cwd=tmp_path,
        env=_with_pip_double(_base_environment(), pip_double),
    )
    assert student.returncode == 0, student.stderr
    student_payload = _read_result(student_result)
    assert _case_names(student_payload) == _case_names(solution_payload)
    assert student_payload["max-score"] == solution_payload["max-score"]
    assert student_payload["score"] <= solution_payload["score"]
