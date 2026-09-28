"""Shared helpers for the Classroom 50 bundle grading tests.

Three test modules drive the bundle-local ``autograder.py`` child against a
staged bundle: ``tests/test_classroom50_native_autograder.py`` (native result and
identity contract), ``tests/test_classroom50_native_bootstrap.py`` (Stage 3
dependency bootstrap), and ``tests/test_classroom50_bundle_stage4.py`` (the real
builder).  Expressing the staged-bundle fixture, the documented native/local
environments, and the canonical result-row rules here keeps the contract
identical in all three so it cannot drift.

The staged fixtures are deliberately *not* shared with the builder: the stage-4
module stages a *source tree* for ``scripts/build_classroom50_bundle.py`` to
consume, while the two native modules stage a *bundle* for a no-argument
invocation.

The staged bundle is a hand-built stand-in for a built bundle.  Its four contract
files are inert placeholders that Stage 3 will replace with the committed
lock-derived requirements, the trusted pytest configuration, the generated
manifest, and the shared validator; Stage 4 hardens the pytest trust boundary and
Stage 5 hardens manifest selection.  The placeholders let the Stage 1/2 contract
be written without waiting for those stages.

``pytest.ini`` is staged deliberately and carries ``--junitxml`` with a
*relative* path.  The in-process native runs of the Stage 3 module use
``pytest.main``, whose rootdir discovery walks up from the collected test paths;
because the staged bundle ships its own ``pytest.ini``, that walk stops inside
the bundle instead of reaching this repository's broad root ``pytest.ini`` and
``conftest.py``.  The junit report the ini requests is written into the run's
working directory, which gives the tests a file to assert on as proof that the
staged ini - and not the repository one - governed the nested run.  The relative
path keeps the ``addopts`` line free of shell quoting.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from tests._classroom50_assignment_contract import (
    ABSENT,
    assignment_type_from_mode,
    username_from_repo,
)

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
AUTOGRADER_SOURCE: Final[Path] = REPO_ROOT / "scripts" / "autograder.py"
RUNTIME_SOURCE: Final[Path] = REPO_ROOT / "exercise_runtime_support"
METADATA_SOURCE: Final[Path] = REPO_ROOT / "exercise_metadata"
REPOSITORY_PYTEST_INI: Final[Path] = REPO_ROOT / "pytest.ini"

DEFAULT_CHILD_TIMEOUT_SECONDS: Final[int] = 120
AUTOGRADER_FILENAME: Final[str] = "autograder.py"
STAGED_INIFILE_PROOF: Final[str] = "staged-inifile-proof.xml"

# A synthetic construct/exercise identity that exists nowhere in the repository, so
# no construct-specific or pilot-specific implementation branch can satisfy the
# Classroom 50 tests.
CONSTRUCT: Final[str] = "sequence"
EXERCISE_KEY: Final[str] = "ex910_sequence_make_native_contract"
EXERCISE_ID: Final[int] = 910
EXERCISE_TITLE: Final[str] = "Native contract fixture"
HIDDEN_TEST_FILENAME: Final[str] = f"test_{EXERCISE_KEY}.py"
PASSING_CASE_IDS: Final[tuple[str, ...]] = ("alpha", "beta")
PASSING_CASE_COUNT: Final[int] = len(PASSING_CASE_IDS)
TEARDOWN_CASE_NAME: Final[str] = "test_call_passes_teardown_fails"
TEARDOWN_CASE_COUNT: Final[int] = 1

RESULT_SCHEMA: Final[str] = "classroom50/result/v1"
GRADING_MANIFEST_SCHEMA: Final[str] = "classroom50/grading-manifest/v1"
NATIVE_RESULT_NAME: Final[str] = "result.json"
LOCAL_RESULT_NAME: Final[str] = "local-result.json"
ACTIVE_VARIANT_ENV_VAR: Final[str] = "PYTUTOR_ACTIVE_VARIANT"

# Documented native environment (SPEC.md, "Invocation and environment contract").
NATIVE_CLASSROOM: Final[str] = "native-contract-classroom"
NATIVE_ASSIGNMENT: Final[str] = "native-contract-assignment"
NATIVE_SUBMISSION_TAG: Final[str] = f"submit/{NATIVE_ASSIGNMENT}-v1"
NATIVE_COMMIT_URL: Final[str] = "https://example.invalid/native/commit"
NATIVE_RELEASE_URL: Final[str] = "https://example.invalid/native/release"
NATIVE_REVIEW_URL: Final[str] = "https://example.invalid/native/review"
NATIVE_MODE: Final[str] = "individual"
NATIVE_OWNER_TAIL: Final[str] = "group-3"
# Upstream repository/actor fixtures (SPEC.md, "Invocation and environment contract").
REPO_CLASSROOM: Final[str] = "py101"
REPO_ASSIGNMENT: Final[str] = "unit3"
GITHUB_ACTOR: Final[str] = "octocat"
# The upstream runner builds the owner identity from the student repository name.
GITHUB_REPOSITORY: Final[str] = f"{NATIVE_CLASSROOM}-{NATIVE_ASSIGNMENT}-{NATIVE_OWNER_TAIL}"
NATIVE_OWNER: Final[str] = username_from_repo(
    GITHUB_REPOSITORY, NATIVE_CLASSROOM, NATIVE_ASSIGNMENT, GITHUB_ACTOR
)
NATIVE_ASSIGNMENT_TYPE: Final[str] = assignment_type_from_mode(NATIVE_MODE)

NATIVE_REQUIRED_ENV: Final[tuple[str, ...]] = (
    "CLASSROOM50_BUNDLE_DIR",
    "CLASSROOM",
    "ASSIGNMENT",
    "ASSIGNMENT_TYPE",
    "SUBMISSION_TAG",
    "COMMIT_URL",
    "RELEASE_URL",
)
NATIVE_OWNER_ENV: Final[tuple[str, ...]] = ("OWNER", "USERNAME")
UNSUPPORTED_ASSIGNMENT_TYPES: Final[tuple[str, ...]] = ("pairs", "solo", "individual-pair")

# Documented local-mode identity values (SPEC.md, "Local mode").
LOCAL_IDENTITY: Final[dict[str, str]] = {
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
ENV_PASSTHROUGH: Final[tuple[str, ...]] = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "TEMP",
    "TMP",
)
LOCAL_VARIANT: Final[str] = "solution"

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

_PLACEHOLDER_REQUIREMENTS = (
    "# Placeholder pins; Stage 3 emits the committed lock-derived requirements.\npytest\n"
)
_PLACEHOLDER_PYTEST_INI = (
    "# Staged bundle configuration.  The junit report is the proof that this file, "
    "not the repository root pytest.ini, governed the run.\n"
    "[pytest]\n"
    f"addopts = -q --junitxml={STAGED_INIFILE_PROOF}\n"
)


@dataclass(frozen=True)
class SyntheticExercise:
    """Identity of one synthetic canonical exercise used by a bundle fixture."""

    exercise_key: str
    exercise_id: int
    construct: str
    title: str
    exercise_type: str = "make"


@dataclass(frozen=True)
class StagedBundle:
    """One staged bundle root plus its synthetic student checkout."""

    bundle: Path
    student: Path

    @property
    def result_path(self) -> Path:
        """Return the native result location inside the student checkout."""
        return self.student / NATIVE_RESULT_NAME


def autograder_source() -> str:
    """Return the current ``scripts/autograder.py`` source text."""
    return AUTOGRADER_SOURCE.read_text(encoding="utf-8")


def run_bundle_child(
    bundle_root: Path,
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = DEFAULT_CHILD_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run the bundle-local ``autograder.py`` child with exactly ``args``.

    Args:
        bundle_root: Directory holding the bundle-local ``autograder.py``.
        args: Exact child argument vector. An empty list is the native invocation.
        cwd: Child working directory; ``None`` inherits the current one.
        env: Child environment; ``None`` inherits the current process environment.
        timeout: Seconds before the child is abandoned.

    Returns:
        The completed child process with captured text streams.
    """
    return subprocess.run(
        [sys.executable, str(bundle_root / AUTOGRADER_FILENAME), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def write_synthetic_exercise_json(exercise_dir: Path, exercise: SyntheticExercise) -> Path:
    """Write a canonical synthetic ``exercise.json`` into ``exercise_dir``.

    The metadata mirrors the field set ``exercise_metadata.loader`` requires, so
    the canonical resolver accepts the synthetic exercise in an isolated
    ``tmp_path`` checkout.

    Args:
        exercise_dir: Canonical exercise directory that receives the file.
        exercise: Identity the written metadata must declare.

    Returns:
        Path to the written ``exercise.json``.
    """
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "exercise_key": exercise.exercise_key,
        "exercise_id": exercise.exercise_id,
        "slug": exercise.exercise_key,
        "title": exercise.title,
        "construct": exercise.construct,
        "exercise_type": exercise.exercise_type,
        "parts": 1,
    }
    path = exercise_dir / "exercise.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    return path


def expected_row_name(exercise_key: str, leaf_node_id: str) -> str:
    """Return the canonical ``<exercise_key>::<leaf-nodeid>`` result-row name.

    The leaf portion is the ``test_*.py::test_name`` tail of the pytest node id
    and never contains an absolute path.
    """
    return f"{exercise_key}::{leaf_node_id}"


def passing_hidden_test_source() -> str:
    """Return the synthetic hidden module whose cases pass in every variant."""
    return _HIDDEN_TEST_PREAMBLE.format(exercise_key=EXERCISE_KEY) + _HIDDEN_TEST_BODY.format(
        case_ids=list(PASSING_CASE_IDS)
    )


def teardown_hidden_test_source() -> str:
    """Return the synthetic hidden module whose call passes and teardown fails."""
    return _TEARDOWN_HIDDEN_TEST


def expected_row_names(case_ids: tuple[str, ...] = PASSING_CASE_IDS) -> list[str]:
    """Return the canonical ``<exercise_key>::<leaf-nodeid>`` row names."""
    return [
        expected_row_name(EXERCISE_KEY, f"{HIDDEN_TEST_FILENAME}::test_native_bundle_case[{case}]")
        for case in case_ids
    ]


def teardown_row_name() -> str:
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
        passing_hidden_test_source(), encoding="utf-8"
    )
    shutil.copytree(METADATA_SOURCE, root / "exercise_metadata")


def _grading_manifest() -> dict[str, Any]:
    """Return the closed placeholder grading manifest for the staged bundle."""
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


def write_placeholder_contract_files(bundle: Path) -> None:
    """Write the four inert bundle contract files that Stage 3 replaces."""
    (bundle / "requirements.txt").write_text(_PLACEHOLDER_REQUIREMENTS, encoding="utf-8")
    (bundle / "pytest.ini").write_text(_PLACEHOLDER_PYTEST_INI, encoding="utf-8")
    (bundle / "classroom50_manifest.py").write_text(
        '"""Placeholder bundle manifest validator; Stage 3 emits the shared one."""\n',
        encoding="utf-8",
    )
    (bundle / "grading_manifest.json").write_text(
        json.dumps(_grading_manifest(), indent=2) + "\n", encoding="utf-8"
    )


def stage_bundle(
    tmp_path: Path,
    *,
    hidden_test_source: str,
    requirements_text: str | None = None,
) -> StagedBundle:
    """Build the minimal staged bundle and synthetic student checkout.

    Args:
        tmp_path: Parent directory that receives the ``student`` and ``bundle`` roots.
        hidden_test_source: Source of the bundled hidden test module.
        requirements_text: Bundle requirements source; defaults to the Stage 1/2
            placeholder.  A native run needs real pins, so the Stage 3 in-process
            runner passes the lock-derived closure instead.

    Returns:
        The staged bundle and its synthetic student checkout.
    """
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
    write_placeholder_contract_files(bundle)
    if requirements_text is not None:
        (bundle / "requirements.txt").write_text(requirements_text, encoding="utf-8")
    return StagedBundle(bundle=bundle, student=student)


def base_child_environment() -> dict[str, str]:
    """Return the minimal, deterministic environment handed to every child."""
    return {key: os.environ[key] for key in ENV_PASSTHROUGH if key in os.environ}


def native_environment(staged: StagedBundle, **overrides: object) -> dict[str, str]:
    """Return the full native environment, applying ``overrides`` (ABSENT removes)."""
    env = base_child_environment()
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


def local_arguments(staged: StagedBundle, result_path: Path, variant: str | None) -> list[str]:
    """Return the documented explicit local argument pair plus an optional variant."""
    args = ["--student-root", str(staged.student), "--result", str(result_path)]
    if variant is not None:
        args.extend(["--variant", variant])
    return args


def run_native_child(staged: StagedBundle, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Invoke the child the way the upstream runner does: no arguments, student cwd."""
    return run_bundle_child(staged.bundle, [], cwd=staged.student, env=env)


def run_local_child(staged: StagedBundle, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the bundle-local child in local mode from the bundle root."""
    return run_bundle_child(
        staged.bundle, list(args), cwd=staged.bundle, env=base_child_environment()
    )


def read_result(result_path: Path) -> dict[str, Any]:
    """Read and parse a written result document."""
    assert result_path.is_file(), f"No result document was written at {result_path}."
    payload: dict[str, Any] = json.loads(result_path.read_text(encoding="utf-8"))
    return payload


def write_stale_result(result_path: Path) -> None:
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
                    for name in expected_row_names()
                ],
            }
        ),
        encoding="utf-8",
    )


def completed_local_result(staged: StagedBundle, result_path: Path) -> dict[str, Any]:
    """Run a local dry-run child with the documented argument pair."""
    proc = run_local_child(staged, *local_arguments(staged, result_path, LOCAL_VARIANT))
    assert proc.returncode == 0, (
        "A local dry-run child must exit 0 for a completed grading run.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    return read_result(result_path)


def assert_canonical_result_fields(payload: dict[str, Any], expected_names: list[str]) -> None:
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
