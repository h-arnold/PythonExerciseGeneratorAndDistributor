"""RED tests for the native Classroom 50 autograder result and identity contract.

This module covers ``ACTION_PLAN.md`` Stage 1 only: the native result schema, the
native environment-source matrix, the documented local identity policy, the
teardown outcome rule, and the pinned native assignment-manifest contract.  No
production code is touched here; several tests are expected to fail until Stage 2
implements native and local autograder modes.

## Why the bundle is staged by hand

Native mode is invoked with no arguments, so the child resolves its own bundle
root from ``CLASSROOM50_BUNDLE_DIR``.  Stage 1 therefore needs *a* bundle, but it
must not depend on anything Stage 3 onwards introduces.  ``_stage_bundle`` builds
a minimal staged bundle in ``tmp_path`` that already satisfies the four bundle
contract files named in ``SPEC.md`` and ``WORKFLOW_SPEC.md``:

- ``autograder.py`` - copied verbatim from ``scripts/autograder.py``;
- ``exercise_runtime_support/`` - a fresh copy of the current runtime source;
- ``exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`` plus its
  ``expectations.py`` support module;
- ``requirements.txt``, ``pytest.ini``, ``grading_manifest.json`` and
  ``classroom50_manifest.py`` - **placeholders only**.

The four contract files are deliberately inert placeholders.  Stage 3 replaces
them with the committed lock-derived requirements, the trusted pytest
configuration, the generated manifest, and the shared validator; Stage 4 hardens
the pytest trust boundary and Stage 5 hardens manifest selection.  Because the
placeholders are already present, the Stage 2 green implementation can be written
and validated without waiting for (or pretending to own) those later stages.

The synthetic exercise key below exists nowhere in the repository, so no
construct-specific or pilot-specific branch can satisfy these tests.

## Contract data versus contract code

Required test cases 8, 9 and the reference halves of 10 and 11 assert *data*
against the rules that ``SPEC.md`` and ``WORKFLOW_SPEC.md`` document, not
against repository production code.  Those rules are transcribed once in
``tests/_classroom50_assignment_contract.py``, which is a transcription of the
documented rules and explicitly not a substitute for the pinned upstream
``schemas/assignments-v1.schema.json``.  ``ACTION_PLAN.md`` Stage 7 pins that
schema (and the upstream ``runner.py``) behind a SHA-256 manifest and must
re-check the transcription against the snapshot.

The native identity constants below are *derived* through that same transcription
rather than hardcoded, so the ``group-<n>`` repository tail is load-bearing. The
behavioural half of cases 10 and 11 - the native result carrying the
``OWNER``/``USERNAME`` pair and the ``individual``/``group``/``team`` result type -
is covered by red tests here.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests._classroom50_assignment_contract import (
    ABSENT,
    ASSIGNMENT_TYPES,
    AUTO_GRADING_MODE,
    DEFAULT_MAX_GROUP_SIZE,
    MAX_MAX_GROUP_SIZE,
    MIN_MAX_GROUP_SIZE,
    OMITTED_FALSE_FLAGS,
    TEAM_FORMATIONS,
    assignment_entry,
    assignment_schema_problems,
    assignment_type_from_mode,
    native_deployment_problems,
    username_from_repo,
    with_overrides,
)
from tests._classroom50_test_helpers import (
    SyntheticExercise,
    expected_row_name,
    run_bundle_child,
    write_synthetic_exercise_json,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOGRADER_SOURCE = REPO_ROOT / "scripts" / "autograder.py"
RUNTIME_SOURCE = REPO_ROOT / "exercise_runtime_support"
METADATA_SOURCE = REPO_ROOT / "exercise_metadata"

# A synthetic construct/exercise identity that exists nowhere in the repository,
# so no construct-specific or pilot-specific implementation branch can satisfy
# these tests.
CONSTRUCT = "sequence"
EXERCISE_KEY = "ex910_sequence_make_native_contract"
EXERCISE_ID = 910
EXERCISE_TITLE = "Native contract fixture"
HIDDEN_TEST_FILENAME = f"test_{EXERCISE_KEY}.py"
PASSING_CASE_IDS = ("alpha", "beta")
PASSING_CASE_COUNT = len(PASSING_CASE_IDS)
TEARDOWN_CASE_NAME = "test_call_passes_teardown_fails"
TEARDOWN_CASE_COUNT = 1

RESULT_SCHEMA = "classroom50/result/v1"
GRADING_MANIFEST_SCHEMA = "classroom50/grading-manifest/v1"
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
NATIVE_RESULT_NAME = "result.json"
LOCAL_RESULT_NAME = "local-result.json"

# Documented native environment (SPEC.md, "Invocation and environment contract").
NATIVE_CLASSROOM = "native-contract-classroom"
NATIVE_ASSIGNMENT = "native-contract-assignment"
NATIVE_SUBMISSION_TAG = f"submit/{NATIVE_ASSIGNMENT}-v1"
NATIVE_COMMIT_URL = "https://example.invalid/native/commit"
NATIVE_RELEASE_URL = "https://example.invalid/native/release"
NATIVE_REVIEW_URL = "https://example.invalid/native/review"
NATIVE_MODE = "individual"
NATIVE_OWNER_TAIL = "group-3"
# Upstream repository/actor fixtures (SPEC.md, "Invocation and environment contract").
REPO_CLASSROOM = "py101"
REPO_ASSIGNMENT = "unit3"
GITHUB_ACTOR = "octocat"
# The upstream runner builds the owner identity from the student repository name.
GITHUB_REPOSITORY = f"{NATIVE_CLASSROOM}-{NATIVE_ASSIGNMENT}-{NATIVE_OWNER_TAIL}"
NATIVE_OWNER = username_from_repo(
    GITHUB_REPOSITORY, NATIVE_CLASSROOM, NATIVE_ASSIGNMENT, GITHUB_ACTOR
)
NATIVE_ASSIGNMENT_TYPE = assignment_type_from_mode(NATIVE_MODE)

NATIVE_REQUIRED_ENV = (
    "CLASSROOM50_BUNDLE_DIR",
    "CLASSROOM",
    "ASSIGNMENT",
    "ASSIGNMENT_TYPE",
    "SUBMISSION_TAG",
    "COMMIT_URL",
    "RELEASE_URL",
)
NATIVE_OWNER_ENV = ("OWNER", "USERNAME")
UNSUPPORTED_ASSIGNMENT_TYPES = ("pairs", "solo", "individual-pair")

# The three grading shapes the pinned schema accepts: explicit auto, an absent
# grading block, and an object whose mode is omitted.
GRADING_SHAPES: tuple[dict[str, Any], ...] = (
    {},
    {"grading": ABSENT},
    {"grading": {}},
)
GRADING_SHAPE_IDS = ("explicit-auto", "grading-absent", "mode-omitted")

# Documented local-mode identity values (SPEC.md, "Local mode").
LOCAL_IDENTITY = {
    "classroom": "local",
    "assignment": "local",
    "assignment_type": "individual",
    "owner": "local",
    "submission": "submit/local",
    "commit": "local://commit",
    "release": "local://release",
    "review": "local://review",
}

# Only these keys reach a child process, so no ambient PYTEST_*/PYTHON_*/PIP_*
# state can influence a graded run.
ENV_PASSTHROUGH = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP")
LOCAL_VARIANT = "solution"

_HIDDEN_TEST_PREAMBLE = '''"""Synthetic hidden test module for the staged native bundle fixture."""

import pytest

from exercise_metadata.resolver import resolve_notebook_path
from exercise_runtime_support.exercise_test_support import load_exercise_test_module

EXERCISE_KEY = {exercise_key!r}
'''

_HIDDEN_TEST_BODY = """

@pytest.mark.parametrize("case", {case_ids!r})
def test_native_bundle_case(case):
    assert load_exercise_test_module(EXERCISE_KEY, "expectations").MARKER == "bundle-hidden"
    notebook = resolve_notebook_path(EXERCISE_KEY, "student")
    assert notebook.name == "student.ipynb"
    assert "student-notebook" in notebook.read_text(encoding="utf-8")
"""

_TEARDOWN_HIDDEN_TEST = '''"""Synthetic hidden test module whose call phase passes and teardown fails."""

import pytest


@pytest.fixture
def failing_teardown():
    yield
    raise RuntimeError("hidden fixture teardown failure")


def test_call_passes_teardown_fails(failing_teardown):
    assert True
'''


@dataclass(frozen=True)
class _StagedBundle:
    """One staged bundle root plus its synthetic student checkout."""

    bundle: Path
    student: Path

    @property
    def result_path(self) -> Path:
        """Return the native result location inside the student checkout."""
        return self.student / NATIVE_RESULT_NAME


def _passing_hidden_test_source() -> str:
    """Return the synthetic hidden module whose cases pass in every variant."""
    return _HIDDEN_TEST_PREAMBLE.format(exercise_key=EXERCISE_KEY) + _HIDDEN_TEST_BODY.format(
        case_ids=list(PASSING_CASE_IDS)
    )


def _expected_row_names(case_ids: tuple[str, ...] = PASSING_CASE_IDS) -> list[str]:
    """Return the canonical ``<exercise_key>::<leaf-nodeid>`` row names."""
    return [
        expected_row_name(EXERCISE_KEY, f"{HIDDEN_TEST_FILENAME}::test_native_bundle_case[{case}]")
        for case in case_ids
    ]


def _teardown_row_name() -> str:
    """Return the canonical row name of the teardown-failure case."""
    return expected_row_name(EXERCISE_KEY, f"{HIDDEN_TEST_FILENAME}::{TEARDOWN_CASE_NAME}")


def _write_synthetic_exercise(root: Path) -> None:
    """Create the canonical student-side exercise surface under ``root``."""
    exercise = root / "exercises" / CONSTRUCT / EXERCISE_KEY
    notebooks = exercise / "notebooks"
    visible_tests = exercise / "tests"
    notebooks.mkdir(parents=True)
    visible_tests.mkdir()
    write_synthetic_exercise_json(
        exercise,
        SyntheticExercise(
            exercise_key=EXERCISE_KEY,
            exercise_id=EXERCISE_ID,
            construct=CONSTRUCT,
            title=EXERCISE_TITLE,
        ),
    )
    for variant in ("student", "solution"):
        (notebooks / f"{variant}.ipynb").write_text(
            json.dumps({"notebook_marker": f"{variant}-notebook"}), encoding="utf-8"
        )
    (visible_tests / HIDDEN_TEST_FILENAME).write_text(
        _passing_hidden_test_source(), encoding="utf-8"
    )
    shutil.copytree(METADATA_SOURCE, root / "exercise_metadata")


def _grading_manifest() -> dict[str, object]:
    """Return the closed placeholder grading manifest for the staged test."""
    return {
        "schema": GRADING_MANIFEST_SCHEMA,
        "exercises": [
            {
                "construct": CONSTRUCT,
                "exercise_key": EXERCISE_KEY,
                "test_path": f"exercises/{CONSTRUCT}/{EXERCISE_KEY}/tests/{HIDDEN_TEST_FILENAME}",
            }
        ],
    }


def _write_placeholder_contract_files(bundle: Path) -> None:
    """Write the four inert bundle contract files that Stage 3 replaces."""
    (bundle / "requirements.txt").write_text(
        "# Placeholder pins; Stage 3 emits the committed lock-derived requirements.\npytest\n",
        encoding="utf-8",
    )
    (bundle / "pytest.ini").write_text(
        "# Placeholder bundle config; Stage 3 emits the trusted pytest file.\n[pytest]\naddopts = -q\n",
        encoding="utf-8",
    )
    (bundle / "classroom50_manifest.py").write_text(
        '"""Placeholder bundle manifest validator; Stage 3 emits the shared one."""\n',
        encoding="utf-8",
    )
    (bundle / "grading_manifest.json").write_text(
        json.dumps(_grading_manifest(), indent=2) + "\n", encoding="utf-8"
    )


def _stage_bundle(tmp_path: Path, *, hidden_test_source: str) -> _StagedBundle:
    """Build the minimal staged bundle and synthetic student checkout."""
    student = tmp_path / "student"
    bundle = tmp_path / "bundle"
    _write_synthetic_exercise(student)

    hidden_tests = bundle / "exercises" / CONSTRUCT / EXERCISE_KEY / "tests"
    hidden_tests.mkdir(parents=True)
    (hidden_tests / HIDDEN_TEST_FILENAME).write_text(hidden_test_source, encoding="utf-8")
    (hidden_tests / "expectations.py").write_text("MARKER = 'bundle-hidden'\n", encoding="utf-8")
    shutil.copytree(
        RUNTIME_SOURCE,
        bundle / "exercise_runtime_support",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy2(AUTOGRADER_SOURCE, bundle / "autograder.py")
    _write_placeholder_contract_files(bundle)
    return _StagedBundle(bundle=bundle, student=student)


@pytest.fixture
def staged_bundle(tmp_path: Path) -> _StagedBundle:
    """Stage a bundle whose two hidden cases pass in every supported variant."""
    return _stage_bundle(tmp_path, hidden_test_source=_passing_hidden_test_source())


def _base_env() -> dict[str, str]:
    """Return the minimal, deterministic environment handed to every child."""
    return {key: os.environ[key] for key in ENV_PASSTHROUGH if key in os.environ}


def _native_env(staged: _StagedBundle, **overrides: object) -> dict[str, str]:
    """Return the full native environment, applying ``overrides`` (ABSENT removes)."""
    env = _base_env()
    env.update(
        {
            "CLASSROOM50_BUNDLE_DIR": str(staged.bundle),
            "CLASSROOM": NATIVE_CLASSROOM,
            "ASSIGNMENT": NATIVE_ASSIGNMENT,
            "ASSIGNMENT_TYPE": NATIVE_ASSIGNMENT_TYPE,
            "MODE": NATIVE_MODE,
            "OWNER": NATIVE_OWNER,
            "USERNAME": NATIVE_OWNER,
            "SUBMISSION_TAG": NATIVE_SUBMISSION_TAG,
            "COMMIT_URL": NATIVE_COMMIT_URL,
            "RELEASE_URL": NATIVE_RELEASE_URL,
            "REVIEW_URL": NATIVE_REVIEW_URL,
            "GITHUB_REPOSITORY": GITHUB_REPOSITORY,
            "GITHUB_ACTOR": GITHUB_ACTOR,
        }
    )
    for key, value in overrides.items():
        if value is ABSENT:
            env.pop(key, None)
        else:
            env[key] = str(value)
    return env


def _local_args(staged: _StagedBundle, result_path: Path, variant: str | None) -> list[str]:
    """Return the documented explicit local argument pair plus an optional variant."""
    args = ["--student-root", str(staged.student), "--result", str(result_path)]
    if variant is not None:
        args.extend(["--variant", variant])
    return args


def _run_native_child(
    staged: _StagedBundle, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Invoke the child the way the upstream runner does: no arguments, student cwd."""
    return run_bundle_child(staged.bundle, [], cwd=staged.student, env=env)


def _run_local_child(staged: _StagedBundle, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the bundle-local child in local mode from the bundle root."""
    return run_bundle_child(staged.bundle, list(args), cwd=staged.bundle, env=_base_env())


def _read_result(result_path: Path) -> dict[str, Any]:
    """Read and parse a written result document."""
    assert result_path.is_file(), f"No result document was written at {result_path}."
    payload: dict[str, Any] = json.loads(result_path.read_text(encoding="utf-8"))
    return payload


def _write_stale_result(result_path: Path) -> None:
    """Write a canonical-shaped but stale child result that must be removed."""
    result_path.write_text(
        json.dumps(
            {
                "schema": RESULT_SCHEMA,
                "classroom": NATIVE_CLASSROOM,
                "assignment": NATIVE_ASSIGNMENT,
                "assignment_type": NATIVE_ASSIGNMENT_TYPE,
                "owner": NATIVE_OWNER,
                "submission": NATIVE_SUBMISSION_TAG,
                "commit": NATIVE_COMMIT_URL,
                "release": NATIVE_RELEASE_URL,
                "review": NATIVE_REVIEW_URL,
                "datetime": "1970-01-01T00:00:00Z",
                "score": PASSING_CASE_COUNT,
                "max-score": PASSING_CASE_COUNT,
                "tests": [
                    {"test-name": name, "passed": True, "score": 1, "max-score": 1}
                    for name in _expected_row_names()
                ],
            }
        ),
        encoding="utf-8",
    )


def _completed_native_result(staged: _StagedBundle, **overrides: object) -> dict[str, Any]:
    """Run a native child with a complete environment and return its result document."""
    proc = _run_native_child(staged, _native_env(staged, **overrides))
    assert proc.returncode == 0, (
        "A native child must exit 0 for a completed grading run.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    return _read_result(staged.result_path)


def _completed_local_result(staged: _StagedBundle, result_path: Path) -> dict[str, Any]:
    """Run a local dry-run child with the documented argument pair."""
    proc = _run_local_child(staged, *_local_args(staged, result_path, LOCAL_VARIANT))
    assert proc.returncode == 0, (
        "A local dry-run child must exit 0 for a completed grading run.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    return _read_result(result_path)


def _assert_canonical_result_fields(payload: dict[str, Any], expected_names: list[str]) -> None:
    """Assert the canonical row shape and the absence of the superseded aliases."""
    assert payload.get("schema") == RESULT_SCHEMA, (
        f"The result must use the canonical 'schema' field; got keys {sorted(payload)}."
    )
    assert "version" not in payload, "The superseded top-level 'version' alias must be gone."
    rows = payload["tests"]
    assert [row.get("test-name") for row in rows] == expected_names, (
        "Every row must use the canonical 'test-name' field."
    )
    assert all("name" not in row for row in rows), "The superseded per-test 'name' alias is gone."
    assert all(isinstance(row.get("passed"), bool) for row in rows), "Every row needs 'passed'."
    assert all(row.get("max-score") == 1 for row in rows)
    assert payload.get("max-score") == len(expected_names)


def _assert_infrastructure_failure(proc: subprocess.CompletedProcess[str], needle: str) -> None:
    """Assert a non-zero child failed clearly, naming ``needle`` in its diagnostics.

    ``SPEC.md`` requires the autograder to "fail clearly" for a missing variable,
    an unsupported assignment type, or absent owner identity.  The wording is not
    pinned, so only the offending variable or value has to appear.
    """
    assert proc.returncode != 0, (
        f"A native identity failure must exit non-zero; expected {needle!r} to be named.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    diagnostics = f"{proc.stdout}\n{proc.stderr}"
    assert "Traceback (most recent call last)" not in diagnostics, (
        f"The child must report a deliberate failure, not crash.\n{diagnostics}"
    )
    assert re.search(rf"\b{re.escape(needle)}\b", diagnostics), (
        f"The failure diagnostics must clearly name {needle!r}.\n{diagnostics}"
    )


# ---------------------------------------------------------------------------
# Cases 1-2: the no-argument native invocation and environment-source matrix.
# ---------------------------------------------------------------------------


def test_native_no_argument_child_writes_result_in_student_checkout(
    staged_bundle: _StagedBundle,
) -> None:
    """A no-argument child writes result.json into the student checkout."""
    proc = _run_native_child(staged_bundle, _native_env(staged_bundle))
    assert proc.returncode == 0, (
        "A no-argument native child must exit 0 for a completed run.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    payload = _read_result(staged_bundle.result_path)
    _assert_canonical_result_fields(payload, _expected_row_names())
    assert payload["score"] == PASSING_CASE_COUNT


def test_native_result_uses_documented_environment_identity_fields(
    staged_bundle: _StagedBundle,
) -> None:
    """Every documented native result field is sourced from its native variable."""
    payload = _completed_native_result(staged_bundle)
    expected = {
        "classroom": NATIVE_CLASSROOM,
        "assignment": NATIVE_ASSIGNMENT,
        "assignment_type": NATIVE_ASSIGNMENT_TYPE,
        "owner": NATIVE_OWNER,
        "submission": NATIVE_SUBMISSION_TAG,
        "commit": NATIVE_COMMIT_URL,
        "release": NATIVE_RELEASE_URL,
        "review": NATIVE_REVIEW_URL,
    }
    wrong = [field for field, value in expected.items() if payload.get(field) != value]
    assert not wrong, f"Native result fields must mirror the native environment: wrong {wrong}."
    datetime_value = payload.get("datetime")
    assert DATETIME_PATTERN.match(str(datetime_value)), (
        f"datetime must be current UTC in YYYY-MM-DDTHH:MM:SSZ form: {datetime_value!r}"
    )


def test_native_review_url_falls_back_to_commit_url(staged_bundle: _StagedBundle) -> None:
    """REVIEW_URL is optional and falls back to COMMIT_URL when it is absent."""
    payload = _completed_native_result(staged_bundle, REVIEW_URL=ABSENT)
    assert payload.get("review") == NATIVE_COMMIT_URL


def test_native_owner_identity_falls_back_from_owner_to_username(
    staged_bundle: _StagedBundle,
) -> None:
    """The result owner falls back to USERNAME when OWNER is absent."""
    payload = _completed_native_result(staged_bundle, OWNER=ABSENT, USERNAME=NATIVE_OWNER)
    assert payload.get("owner") == NATIVE_OWNER


# ---------------------------------------------------------------------------
# Case 3: missing or unsupported native identity is a non-zero infrastructure error.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing", NATIVE_REQUIRED_ENV + NATIVE_OWNER_ENV)
def test_native_missing_required_variable_fails_and_removes_stale_result(
    staged_bundle: _StagedBundle,
    missing: str,
) -> None:
    """A missing required native variable is non-zero, clear, and clears a stale result."""
    _write_stale_result(staged_bundle.result_path)
    proc = _run_native_child(staged_bundle, _native_env(staged_bundle, **{missing: ABSENT}))
    assert proc.returncode != 0, (
        f"Missing {missing} must be an infrastructure failure with a non-zero exit.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert not staged_bundle.result_path.exists(), (
        f"A stale result must not survive the missing-{missing} infrastructure failure."
    )
    _assert_infrastructure_failure(proc, missing)


def test_native_missing_both_owner_variables_fails_and_removes_stale_result(
    staged_bundle: _StagedBundle,
) -> None:
    """Dropping both OWNER and USERNAME is a non-zero infrastructure failure."""
    _write_stale_result(staged_bundle.result_path)
    env = _native_env(staged_bundle, OWNER=ABSENT, USERNAME=ABSENT)
    proc = _run_native_child(staged_bundle, env)
    assert proc.returncode != 0, proc.stderr
    assert not staged_bundle.result_path.exists(), (
        "A stale result must not survive the missing-owner-identity failure."
    )
    _assert_infrastructure_failure(proc, "OWNER")


@pytest.mark.parametrize("assignment_type", UNSUPPORTED_ASSIGNMENT_TYPES)
def test_native_unsupported_assignment_type_fails_and_removes_stale_result(
    staged_bundle: _StagedBundle,
    assignment_type: str,
) -> None:
    """An unsupported ASSIGNMENT_TYPE is a non-zero, clearly-reported failure."""
    _write_stale_result(staged_bundle.result_path)
    env = _native_env(staged_bundle, ASSIGNMENT_TYPE=assignment_type)
    proc = _run_native_child(staged_bundle, env)
    assert proc.returncode != 0, (
        f"ASSIGNMENT_TYPE={assignment_type!r} must be rejected as unsupported.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert not staged_bundle.result_path.exists(), (
        f"A stale result must not survive the unsupported-{assignment_type} failure."
    )
    _assert_infrastructure_failure(proc, assignment_type)


# ---------------------------------------------------------------------------
# Cases 4-6: local mode arguments, local identity values, canonical field names.
# ---------------------------------------------------------------------------


def test_local_mode_accepts_both_arguments_as_a_required_pair(
    staged_bundle: _StagedBundle,
) -> None:
    """The explicit pair selects local mode and writes the canonical result."""
    payload = _completed_local_result(staged_bundle, staged_bundle.bundle / LOCAL_RESULT_NAME)
    _assert_canonical_result_fields(payload, _expected_row_names())
    assert payload["score"] == PASSING_CASE_COUNT


@pytest.mark.parametrize("lonely_argument", ("--student-root", "--result"))
def test_local_mode_rejects_a_single_argument_without_writing_a_result(
    staged_bundle: _StagedBundle,
    lonely_argument: str,
) -> None:
    """Either local argument alone is rejected and no result is written anywhere.

    This guards the Stage 2 change that makes both arguments individually
    optional: the pair requirement has to survive that change, and a lone
    argument must not silently fall through to native mode and write a result
    into the student checkout.
    """
    result_path = staged_bundle.bundle / LOCAL_RESULT_NAME
    value = str(staged_bundle.student) if lonely_argument == "--student-root" else str(result_path)
    proc = _run_local_child(staged_bundle, lonely_argument, value)
    assert proc.returncode != 0, (
        f"{lonely_argument} supplied alone must be rejected.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert not result_path.exists()
    assert not (staged_bundle.bundle / NATIVE_RESULT_NAME).exists()
    assert not staged_bundle.result_path.exists()


def test_local_result_uses_exact_documented_local_identity_values(
    staged_bundle: _StagedBundle,
) -> None:
    """Local mode emits the exact documented non-uploadable identity values."""
    payload = _completed_local_result(staged_bundle, staged_bundle.bundle / LOCAL_RESULT_NAME)
    wrong = [field for field, expected in LOCAL_IDENTITY.items() if payload.get(field) != expected]
    assert not wrong, f"Local identity fields must match SPEC.md exactly; wrong: {wrong}."
    datetime_value = payload.get("datetime")
    assert DATETIME_PATTERN.match(str(datetime_value)), (
        f"Local datetime must be current UTC in YYYY-MM-DDTHH:MM:SSZ form: {datetime_value!r}"
    )


def test_native_result_uses_canonical_field_names_without_old_aliases(
    staged_bundle: _StagedBundle,
) -> None:
    """The native payload uses schema/test-name/passed and no superseded aliases."""
    payload = _completed_native_result(staged_bundle)
    _assert_canonical_result_fields(payload, _expected_row_names())


def test_local_result_uses_canonical_field_names_without_old_aliases(
    staged_bundle: _StagedBundle,
) -> None:
    """The local payload uses schema/test-name/passed and no superseded aliases."""
    payload = _completed_local_result(staged_bundle, staged_bundle.bundle / LOCAL_RESULT_NAME)
    _assert_canonical_result_fields(payload, _expected_row_names())


# ---------------------------------------------------------------------------
# Case 7: a passing call phase with a failing teardown is scored as failed.
# ---------------------------------------------------------------------------


def test_passing_call_with_failing_teardown_is_scored_as_failed(tmp_path: Path) -> None:
    """A teardown failure cannot be discarded in favour of an earlier call-phase pass.

    The score assertions come first and use field names that the superseded
    result shape also carries, so the only reason this can fail is the teardown
    outcome rule itself.
    """
    staged = _stage_bundle(tmp_path, hidden_test_source=_TEARDOWN_HIDDEN_TEST)
    payload = _completed_local_result(staged, staged.bundle / LOCAL_RESULT_NAME)
    assert payload["max-score"] == TEARDOWN_CASE_COUNT
    assert payload["score"] == 0, (
        "A test whose call phase passes but whose teardown fails must not score a point."
    )
    row = payload["tests"][0]
    assert row["max-score"] == TEARDOWN_CASE_COUNT
    assert row["score"] == 0
    assert row["passed"] is False, "The teardown failure must be reported as not passed."
    assert row["test-name"] == _teardown_row_name()


# ---------------------------------------------------------------------------
# Cases 8-9: the transcribed native assignment-manifest schema and deployment rules.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ASSIGNMENT_TYPES)
@pytest.mark.parametrize("grading_shape", GRADING_SHAPES, ids=GRADING_SHAPE_IDS)
def test_valid_native_assignment_manifest_fixtures_satisfy_the_pinned_schema(
    mode: str,
    grading_shape: dict[str, Any],
) -> None:
    """Individual, group, and team fixtures satisfy every transcribed pinned rule."""
    entry = with_overrides(assignment_entry(mode), **grading_shape)
    assert assignment_schema_problems(entry) == []
    assert native_deployment_problems(entry) == []


@pytest.mark.parametrize("flag", OMITTED_FALSE_FLAGS)
def test_explicit_false_flags_are_accepted(flag: str) -> None:
    """A flag documented as "false or omitted" accepts an explicit false."""
    entry = with_overrides(assignment_entry("individual"), **{flag: False})
    assert assignment_schema_problems(entry) == []
    assert native_deployment_problems(entry) == []


def test_an_explicitly_disabled_init_shim_keeps_a_valid_template() -> None:
    """`init_shim: false` with a template stays a valid, deployable native entry."""
    entry = with_overrides(assignment_entry("individual"), init_shim=False)
    assert assignment_schema_problems(entry) == []
    assert native_deployment_problems(entry) == []


def test_the_three_accepted_grading_shapes_are_distinct_fixtures() -> None:
    """Explicit auto, absent grading, and omitted mode are three different documents."""
    explicit_auto, grading_absent, mode_omitted = (
        with_overrides(assignment_entry("individual"), **shape) for shape in GRADING_SHAPES
    )
    assert explicit_auto["grading"] == {"mode": AUTO_GRADING_MODE}
    assert "grading" not in grading_absent
    assert mode_omitted["grading"] == {}
    documents = {
        json.dumps(entry, sort_keys=True) for entry in (explicit_auto, grading_absent, mode_omitted)
    }
    assert len(documents) == len(GRADING_SHAPES), (
        "The accepted grading shapes must produce distinct fixtures, not duplicates."
    )


@pytest.mark.parametrize(
    ("overrides", "expected_problems"),
    [
        ({"slug": ABSENT}, ["slug must be a non-empty string"]),
        ({"slug": "   "}, ["slug must be a non-empty string"]),
        ({"slug": 7}, ["slug must be a non-empty string"]),
        ({"name": ""}, ["name must be a non-empty string"]),
        ({"name": ABSENT}, ["name must be a non-empty string"]),
        ({"autograder": "python"}, ["autograder must be the string 'default'"]),
        ({"autograder": ABSENT}, ["autograder must be the string 'default'"]),
        ({"grading": {"mode": "off"}}, ["grading.mode must be 'auto' or omitted"]),
        ({"grading": {"mode": "manual"}}, ["grading.mode must be 'auto' or omitted"]),
        ({"grading": {"mode": True}}, ["grading.mode must be 'auto' or omitted"]),
        ({"grading": "auto"}, ["grading must be an object when present"]),
        ({"grading": None}, ["grading must be an object when present"]),
        ({"tests": [{"command": "pytest"}]}, ["tests must be absent"]),
        ({"empty_repo": True}, ["empty_repo must be false or omitted"]),
        ({"empty_repo": "yes"}, ["empty_repo must be a boolean when present"]),
        ({"no_autograder": True}, ["no_autograder must be false or omitted"]),
        ({"no_autograder": "no"}, ["no_autograder must be a boolean when present"]),
        ({"mode": "pairs"}, ["mode must be one of ('individual', 'group', 'team'), got 'pairs'"]),
        ({"mode": ABSENT}, ["mode must be one of ('individual', 'group', 'team'), got None"]),
    ],
)
def test_invalid_assignment_manifest_combinations_are_rejected(
    overrides: dict[str, Any],
    expected_problems: list[str],
) -> None:
    """Invalid required fields, flags, grading shapes, and modes are rejected exactly."""
    entry = with_overrides(assignment_entry("individual"), **overrides)
    assert assignment_schema_problems(entry) == expected_problems


@pytest.mark.parametrize(
    ("mode", "overrides", "expected_problems"),
    [
        (
            "individual",
            {"max_group_size": DEFAULT_MAX_GROUP_SIZE},
            ["individual must omit max_group_size"],
        ),
        ("individual", {"team_formation": "teacher"}, ["individual must omit team_formation"]),
        (
            "group",
            {"max_group_size": ABSENT},
            ["group requires an integer max_group_size in 2-100"],
        ),
        ("group", {"max_group_size": "3"}, ["group requires an integer max_group_size in 2-100"]),
        ("group", {"max_group_size": True}, ["group requires an integer max_group_size in 2-100"]),
        ("group", {"max_group_size": 1}, ["max_group_size must be within 2-100"]),
        ("group", {"max_group_size": 101}, ["max_group_size must be within 2-100"]),
        ("group", {"team_formation": "teacher"}, ["group must omit team_formation"]),
        ("team", {"max_group_size": ABSENT}, ["team requires an integer max_group_size in 2-100"]),
        ("team", {"max_group_size": 101}, ["max_group_size must be within 2-100"]),
        (
            "team",
            {"team_formation": ABSENT},
            ["team_formation must be one of ('teacher', 'student')"],
        ),
        (
            "team",
            {"team_formation": "manager"},
            ["team_formation must be one of ('teacher', 'student')"],
        ),
        (
            "team",
            {"team_formation": True},
            ["team_formation must be one of ('teacher', 'student')"],
        ),
    ],
)
def test_invalid_group_and_team_conditional_fields_are_rejected(
    mode: str,
    overrides: dict[str, Any],
    expected_problems: list[str],
) -> None:
    """The conditional group/team fields are enforced exactly at the documented bounds."""
    entry = with_overrides(assignment_entry(mode), **overrides)
    assert assignment_schema_problems(entry) == expected_problems


def test_minimum_and_maximum_group_sizes_are_accepted() -> None:
    """The max_group_size bounds are inclusive at 2 and 100."""
    for max_group_size in (MIN_MAX_GROUP_SIZE, MAX_MAX_GROUP_SIZE):
        entry = with_overrides(assignment_entry("group"), max_group_size=max_group_size)
        assert assignment_schema_problems(entry) == []


@pytest.mark.parametrize("team_formation", TEAM_FORMATIONS)
def test_both_team_formation_values_are_accepted(team_formation: str) -> None:
    """team_formation accepts exactly teacher and student."""
    entry = with_overrides(assignment_entry("team"), team_formation=team_formation)
    assert assignment_schema_problems(entry) == []


@pytest.mark.parametrize(
    ("overrides", "expected_problems"),
    [
        ({"init_shim": True}, ["init_shim and template are mutually exclusive"]),
        (
            {"init_shim": True, "empty_repo": True},
            [
                "empty_repo must be false or omitted",
                "init_shim and template are mutually exclusive",
                "init_shim excludes empty_repo",
            ],
        ),
        (
            {"init_shim": True, "no_autograder": True},
            [
                "no_autograder must be false or omitted",
                "init_shim and template are mutually exclusive",
                "init_shim excludes no_autograder",
            ],
        ),
    ],
)
def test_schema_negative_init_shim_combinations_are_rejected(
    overrides: dict[str, Any],
    expected_problems: list[str],
) -> None:
    """template/init_shim, init_shim/empty_repo, and init_shim/no_autograder are invalid."""
    entry = with_overrides(assignment_entry("individual"), **overrides)
    assert assignment_schema_problems(entry) == expected_problems


def test_init_shim_assignment_is_schema_valid_but_unsupported_for_native_deployment() -> None:
    """init_shim stays a schema fixture yet is rejected as a native deployment."""
    entry = with_overrides(assignment_entry("individual"), template=ABSENT, init_shim=True)
    assert assignment_schema_problems(entry) == []
    assert native_deployment_problems(entry) == [
        "init_shim is unsupported for the native bundle deployment",
        "native deployment requires a template with non-empty owner, repo, and branch",
    ]


def test_templated_native_assignment_is_deployable_for_every_supported_mode() -> None:
    """A valid templated assignment passes the native deployment rules."""
    for mode in ASSIGNMENT_TYPES:
        entry = assignment_entry(mode)
        assert native_deployment_problems(entry) == [], mode


@pytest.mark.parametrize(
    "template",
    [
        ABSENT,
        {},
        {"owner": "classroom50-fixture"},
        {"repo": "native-starter-template", "branch": ""},
        {"owner": 1, "repo": 2, "branch": 3},
        "classroom50-fixture/native-starter-template",
    ],
    ids=("absent", "empty", "missing-branch", "blank-branch", "non-string", "not-an-object"),
)
def test_native_deployment_requires_a_complete_template(template: Any) -> None:
    """A native deployment requires a template with non-empty string owner/repo/branch."""
    entry = with_overrides(assignment_entry("individual"), template=template)
    assert native_deployment_problems(entry) == [
        "native deployment requires a template with non-empty owner, repo, and branch"
    ]


# ---------------------------------------------------------------------------
# Case 10: upstream repository-name derivation and the OWNER/USERNAME pair.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("repository", "expected_owner"),
    [
        (f"{REPO_CLASSROOM}-{REPO_ASSIGNMENT}-marie", "marie"),
        (f"{REPO_CLASSROOM.upper()}-{REPO_ASSIGNMENT.upper()}-marie", "marie"),
        (f"{REPO_CLASSROOM}-{REPO_ASSIGNMENT}-Marie", "Marie"),
        (f"{REPO_CLASSROOM}-{REPO_ASSIGNMENT}-group-2", "group-2"),
        (f"{REPO_CLASSROOM}-{REPO_ASSIGNMENT}-team-4", "team-4"),
        (f"{REPO_CLASSROOM}-{REPO_ASSIGNMENT}-", GITHUB_ACTOR),
        (f"{REPO_ASSIGNMENT}-marie", GITHUB_ACTOR),
        ("some-other-repository", GITHUB_ACTOR),
    ],
)
def test_username_from_repo_transcription_matches_documented_cases(
    repository: str,
    expected_owner: str,
) -> None:
    """The transcribed derivation strips the expected prefix case-insensitively.

    ``SPEC.md`` (section "Invocation and environment contract") records that the
    ``<classroom>-<assignment>-`` prefix is removed without regard to case, the
    remaining repository tail is used verbatim (including ``group-<n>`` and
    ``team-<n>`` tails), and the GitHub actor is the fallback.
    """
    derived = username_from_repo(repository, REPO_CLASSROOM, REPO_ASSIGNMENT, GITHUB_ACTOR)
    assert derived == expected_owner


def test_native_owner_identity_is_derived_from_the_student_repository_name() -> None:
    """The fixture owner comes from the group tail, not a hardcoded literal."""
    expected_repository = f"{NATIVE_CLASSROOM}-{NATIVE_ASSIGNMENT}-{NATIVE_OWNER_TAIL}"
    derived_owner = username_from_repo(
        expected_repository, NATIVE_CLASSROOM, NATIVE_ASSIGNMENT, GITHUB_ACTOR
    )
    assert derived_owner == NATIVE_OWNER_TAIL
    assert derived_owner == NATIVE_OWNER
    assert derived_owner == "group-3"
    assert assignment_type_from_mode(NATIVE_MODE) == NATIVE_ASSIGNMENT_TYPE
    assert assignment_type_from_mode(NATIVE_MODE) == "individual"


def test_native_owner_and_username_are_identical_in_native_mode(
    staged_bundle: _StagedBundle,
) -> None:
    """The upstream runner sets OWNER and USERNAME to one repository identity."""
    env = _native_env(staged_bundle)
    assert env["GITHUB_REPOSITORY"] == GITHUB_REPOSITORY
    assert env["OWNER"] == env["USERNAME"] == NATIVE_OWNER
    payload = _completed_native_result(staged_bundle)
    assert payload.get("owner") == env["OWNER"] == env["USERNAME"]


# ---------------------------------------------------------------------------
# Case 11: MODE normalisation to the individual/group/team result type.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ASSIGNMENT_TYPES)
def test_mode_normalisation_transcription_maps_supported_modes_to_assignment_types(
    mode: str,
) -> None:
    """The transcribed normalisation maps each supported MODE onto its result type.

    Only the identity mapping is transcribed: ``SPEC.md`` (section "Invocation
    and environment contract") records that ``ASSIGNMENT_TYPE`` is normalised
    from the runner's ``MODE`` value and that the supported set is exactly
    ``individual``, ``group``, and ``team``. Whitespace trimming and case folding
    are not specified, so they are deliberately not asserted.
    """
    assert assignment_type_from_mode(mode) == mode


@pytest.mark.parametrize("mode", UNSUPPORTED_ASSIGNMENT_TYPES)
def test_mode_normalisation_transcription_rejects_unsupported_modes(mode: str) -> None:
    """An unsupported MODE value cannot normalise to a supported result type."""
    with pytest.raises(ValueError, match="Unsupported MODE value"):
        assignment_type_from_mode(mode)


@pytest.mark.parametrize("mode", ASSIGNMENT_TYPES)
def test_native_result_preserves_individual_group_and_team_assignment_type(
    staged_bundle: _StagedBundle,
    mode: str,
) -> None:
    """Native grading preserves the individual/group/team identity from the environment."""
    payload = _completed_native_result(
        staged_bundle,
        MODE=mode,
        ASSIGNMENT_TYPE=assignment_type_from_mode(mode),
    )
    assert payload.get("assignment_type") == mode
    _assert_canonical_result_fields(payload, _expected_row_names())
