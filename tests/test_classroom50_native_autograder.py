"""Contract tests for the native Classroom 50 autograder result and identity behaviour.

This module owns the ``ACTION_PLAN.md`` Stage 1 and Stage 2 contracts: the native
result schema, the native environment-source matrix, the two invocation modes, the
teardown outcome rule, and the transcribed native assignment-manifest rules.  The
Stage 3 dependency bootstrap lives in
``tests/test_classroom50_native_bootstrap.py``.

## Which runs are in-process and which are real child processes

A *completed* native run has to install the bundle requirements into a fresh
bundle-local target, and this repository's virtual environment cannot do that: it
has no ``pip``, the fixed argv Stage 3 pins has no offline switch, the mandatory
``PIP_*`` scrub rules out ``PIP_NO_INDEX``/``PIP_FIND_LINKS``, and a monkeypatch
cannot cross a process boundary.  The native *success* assertions therefore invoke
the child's own entry point, ``main([])``, in-process with the pip subprocess
faked: real pytest still collects and runs the hidden tests and the canonical
result is still written to the student checkout, only the operating-system process
boundary is given up.  The seam contract that fake implements is documented in
``tests/_classroom50_bootstrap.py``.

Real child subprocesses are kept where they are meaningful and affordable: the
native *failure* paths that fail during environment validation or the
package-origin check, before any install, plus every local dry run, which never
bootstraps.

## The staged bundle

``tests/_classroom50_test_helpers.py`` owns the staged bundle: the synthetic
student checkout, the bundle-local copies of the grader and the runtime package,
and the four inert contract-file placeholders (``requirements.txt``,
``pytest.ini``, ``grading_manifest.json``, ``classroom50_manifest.py``) that Stage
3 replaces and Stages 4 and 5 harden.

The synthetic exercise key that staged bundle uses exists nowhere in the
repository, so no construct-specific or pilot-specific implementation branch can
satisfy these tests.

## Contract data versus contract code

Required test cases 8, 9 and the reference halves of 10 and 11 assert *data*
against the rules that ``SPEC.md`` and ``WORKFLOW_SPEC.md`` document, not against
repository production code.  Those rules are transcribed once in
``tests/_classroom50_assignment_contract.py``, which is a transcription of the
documented rules and explicitly not a substitute for the pinned upstream
``schemas/assignments-v1.schema.json``.  ``ACTION_PLAN.md`` Stage 7 pins that
schema (and the upstream ``runner.py``) behind a SHA-256 manifest and must re-check
the transcription against the snapshot.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable
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
from tests._classroom50_bootstrap import load_bundle_autograder, run_native_in_process
from tests._classroom50_test_helpers import (
    AUTOGRADER_SOURCE,
    DEFAULT_CHILD_TIMEOUT_SECONDS,
    GITHUB_ACTOR,
    GITHUB_REPOSITORY,
    LOCAL_IDENTITY,
    LOCAL_RESULT_NAME,
    LOCAL_VARIANT,
    NATIVE_ASSIGNMENT,
    NATIVE_ASSIGNMENT_TYPE,
    NATIVE_CLASSROOM,
    NATIVE_COMMIT_URL,
    NATIVE_MODE,
    NATIVE_OWNER,
    NATIVE_OWNER_ENV,
    NATIVE_OWNER_TAIL,
    NATIVE_RELEASE_URL,
    NATIVE_REQUIRED_ENV,
    NATIVE_RESULT_NAME,
    NATIVE_REVIEW_URL,
    NATIVE_SUBMISSION_TAG,
    PASSING_CASE_COUNT,
    REPO_ASSIGNMENT,
    REPO_CLASSROOM,
    REPO_ROOT,
    TEARDOWN_CASE_COUNT,
    UNSUPPORTED_ASSIGNMENT_TYPES,
    StagedBundle,
    assert_canonical_result_fields,
    base_child_environment,
    completed_local_result,
    expected_row_names,
    local_arguments,
    native_environment,
    passing_hidden_test_source,
    read_result,
    run_local_child,
    run_native_child,
    stage_bundle,
    teardown_hidden_test_source,
    teardown_row_name,
    write_stale_result,
)

DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# The exit status ``scripts/autograder.py`` returns for every declared
# infrastructure failure: identity, package origin, or dependency bootstrap.
INFRASTRUCTURE_EXIT_CODE = 2

# The three grading shapes the pinned schema accepts: explicit auto, an absent
# grading block, and an object whose mode is omitted.
GRADING_SHAPES: tuple[dict[str, Any], ...] = (
    {},
    {"grading": ABSENT},
    {"grading": {}},
)
GRADING_SHAPE_IDS = ("explicit-auto", "grading-absent", "mode-omitted")


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


def _raiser(failure: BaseException) -> Callable[..., Any]:
    """Return a ``run_bundle`` stand-in that raises ``failure`` when called."""

    def _fail(*args: Any, **kwargs: Any) -> Any:
        raise failure

    return _fail


@pytest.fixture
def staged_bundle(tmp_path: Path) -> StagedBundle:
    """Stage a bundle whose two hidden cases pass in every supported variant."""
    return stage_bundle(tmp_path, hidden_test_source=passing_hidden_test_source())


def _completed_native_result(
    staged: StagedBundle, monkeypatch: pytest.MonkeyPatch, **overrides: object
) -> dict[str, Any]:
    """Run the native entry point in-process with a faked install; return its result.

    The pip subprocess is faked, so the run needs neither ``pip`` nor a package
    index; everything else - environment validation, the fresh-target bootstrap,
    pytest collection, and the canonical result document - is the real code path.
    """
    run = run_native_in_process(monkeypatch, staged, env_overrides=overrides or None)
    assert run.exit_code == 0, (
        f"A completed native run must exit 0, not {run.exit_code}; "
        f"environment overrides {sorted(overrides)}."
    )
    return read_result(staged.result_path)


# ---------------------------------------------------------------------------
# Cases 1-2: the no-argument native invocation and environment-source matrix.
# ---------------------------------------------------------------------------


def test_native_no_argument_child_writes_result_in_student_checkout(
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A no-argument native run writes result.json into the student checkout.

    The child's own entry point, ``main([])``, is invoked in-process because a
    completed native run has to install the bundle requirements, which this
    repository's pip-less virtual environment cannot do; see the seam contract in
    ``tests/_classroom50_bootstrap.py``.
    """
    run = run_native_in_process(monkeypatch, staged_bundle)
    assert run.exit_code == 0, f"A no-argument native run must exit 0, not {run.exit_code}."
    payload = read_result(staged_bundle.result_path)
    assert_canonical_result_fields(payload, expected_row_names())
    assert payload["score"] == PASSING_CASE_COUNT


def test_native_result_uses_documented_environment_identity_fields(
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every documented native result field is sourced from its native variable."""
    payload = _completed_native_result(staged_bundle, monkeypatch)
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


def test_native_review_url_falls_back_to_commit_url(
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REVIEW_URL is optional and falls back to COMMIT_URL when it is absent."""
    payload = _completed_native_result(staged_bundle, monkeypatch, REVIEW_URL=ABSENT)
    assert payload.get("review") == NATIVE_COMMIT_URL


def test_native_owner_identity_falls_back_from_owner_to_username(
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The result owner falls back to USERNAME when OWNER is absent."""
    payload = _completed_native_result(staged_bundle, monkeypatch, OWNER=ABSENT)
    assert payload.get("owner") == NATIVE_OWNER


# ---------------------------------------------------------------------------
# Case 3: missing or unsupported native identity is a non-zero infrastructure error.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing", NATIVE_REQUIRED_ENV)
def test_native_missing_required_variable_fails_and_removes_stale_result(
    staged_bundle: StagedBundle,
    missing: str,
) -> None:
    """A missing required native variable is non-zero, clear, and clears a stale result.

    Only the unconditionally required variables are parametrised here.  The two
    owner variables are a documented pair, not two required values: SPEC.md
    requires "at least one of ``OWNER`` and ``USERNAME``" and states that
    "``OWNER`` ... [is] required if ``USERNAME`` is absent" and vice versa, so
    dropping exactly one of them is the owner fallback covered by
    ``test_native_owner_identity_falls_back_from_owner_to_username`` and
    ``test_native_review_url_falls_back_to_commit_url``.  Dropping both is the
    separate failure asserted below.
    """
    write_stale_result(staged_bundle.result_path)
    proc = run_native_child(staged_bundle, native_environment(staged_bundle, **{missing: ABSENT}))
    assert proc.returncode != 0, (
        f"Missing {missing} must be an infrastructure failure with a non-zero exit.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert not staged_bundle.result_path.exists(), (
        f"A stale result must not survive the missing-{missing} infrastructure failure."
    )
    _assert_infrastructure_failure(proc, missing)


def test_native_missing_both_owner_variables_fails_and_removes_stale_result(
    staged_bundle: StagedBundle,
) -> None:
    """Dropping both OWNER and USERNAME is a non-zero infrastructure failure."""
    write_stale_result(staged_bundle.result_path)
    env = native_environment(staged_bundle, **{name: ABSENT for name in NATIVE_OWNER_ENV})
    proc = run_native_child(staged_bundle, env)
    assert proc.returncode != 0, proc.stderr
    assert not staged_bundle.result_path.exists(), (
        "A stale result must not survive the missing-owner-identity failure."
    )
    _assert_infrastructure_failure(proc, "OWNER")


@pytest.mark.parametrize("assignment_type", UNSUPPORTED_ASSIGNMENT_TYPES)
def test_native_unsupported_assignment_type_fails_and_removes_stale_result(
    staged_bundle: StagedBundle,
    assignment_type: str,
) -> None:
    """An unsupported ASSIGNMENT_TYPE is a non-zero, clearly-reported failure."""
    write_stale_result(staged_bundle.result_path)
    env = native_environment(staged_bundle, ASSIGNMENT_TYPE=assignment_type)
    proc = run_native_child(staged_bundle, env)
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
    staged_bundle: StagedBundle,
) -> None:
    """The explicit pair selects local mode and writes the canonical result."""
    payload = completed_local_result(staged_bundle, staged_bundle.bundle / LOCAL_RESULT_NAME)
    assert_canonical_result_fields(payload, expected_row_names())
    assert payload["score"] == PASSING_CASE_COUNT


@pytest.mark.parametrize("lonely_argument", ("--student-root", "--result"))
def test_local_mode_rejects_a_single_argument_without_writing_a_result(
    staged_bundle: StagedBundle,
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
    proc = run_local_child(staged_bundle, lonely_argument, value)
    assert proc.returncode != 0, (
        f"{lonely_argument} supplied alone must be rejected.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert not result_path.exists()
    assert not (staged_bundle.bundle / NATIVE_RESULT_NAME).exists()
    assert not staged_bundle.result_path.exists()


def test_local_only_variant_flag_is_rejected_without_the_local_argument_pair(
    staged_bundle: StagedBundle,
) -> None:
    """``--variant`` alone cannot select native mode and write a result.

    ``--variant solution`` is documented as local dry-run only.  Accepting it
    without the argument pair would silently produce a native, upload-shaped
    grade for the student variant, so it is a usage error instead.
    """
    proc = run_local_child(staged_bundle, "--variant", LOCAL_VARIANT)
    assert proc.returncode != 0, (
        "--variant without the local pair must be rejected.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    assert not (staged_bundle.bundle / NATIVE_RESULT_NAME).exists()
    assert not staged_bundle.result_path.exists()


def test_in_place_script_execution_is_not_a_supported_local_mode(
    staged_bundle: StagedBundle,
) -> None:
    """``scripts/autograder.py`` in place cannot grade: the bundle root is its parent.

    Local mode resolves the bundle root from the script parent, so an in-place
    copy has no ``exercise_runtime_support/`` beside it and the package-origin
    check refuses the run instead of silently grading the wrong surface.
    """
    result_path = staged_bundle.bundle / LOCAL_RESULT_NAME
    proc = subprocess.run(
        [
            sys.executable,
            str(AUTOGRADER_SOURCE),
            "--student-root",
            str(staged_bundle.student),
            "--result",
            str(result_path),
        ],
        cwd=REPO_ROOT,
        env=base_child_environment(),
        capture_output=True,
        text=True,
        timeout=DEFAULT_CHILD_TIMEOUT_SECONDS,
        check=False,
    )
    assert proc.returncode != 0, "In-place execution must not grade a checkout."
    assert not result_path.exists()
    _assert_infrastructure_failure(proc, "exercise_runtime_support")


@pytest.mark.parametrize(
    "error_name",
    ["GradingConfigurationError", "PackageOriginError", "DependencyBootstrapError"],
    ids=("configuration", "origin", "dependencies"),
)
def test_main_converts_a_declared_infrastructure_failure_into_exit_two(
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch, error_name: str
) -> None:
    """A declared failure is reported; it never escapes as an unhandled exception.

    ``main`` narrows its reported failures to ``GradingInfrastructureError`` so an
    unrelated exception cannot be mislabelled as a deliberate infrastructure failure
    with no diagnostic. Each declared type must therefore still be converted into a
    clean exit 2, and the result output must be left absent. The exception classes are
    read from the bundle-local grader, because that is the module instance whose
    ``main`` is being driven.
    """
    module = load_bundle_autograder(monkeypatch, staged_bundle.bundle)
    monkeypatch.setattr(module, "run_bundle", _raiser(getattr(module, error_name)(error_name)))
    result_path = staged_bundle.bundle / LOCAL_RESULT_NAME
    exit_code = module.main(local_arguments(staged_bundle, result_path, None))
    assert exit_code == INFRASTRUCTURE_EXIT_CODE, (
        f"a declared failure must exit {INFRASTRUCTURE_EXIT_CODE}, not {exit_code}"
    )
    assert not result_path.exists(), "a declared failure must write no completed result"


def test_main_lets_an_undeclared_runtime_failure_propagate(
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An exception outside the declared types is a bug, so it surfaces as a traceback.

    This is the half of the narrowed catch that keeps real defects visible: pytest
    internals, the runtime package, or the grader's own code raising a bare
    ``RuntimeError`` must not be reported as an infrastructure failure with no
    diagnostic detail. The outer runner still treats the resulting non-zero child exit
    as an error, so nothing is graded either way.
    """
    module = load_bundle_autograder(monkeypatch, staged_bundle.bundle)
    monkeypatch.setattr(module, "run_bundle", _raiser(RuntimeError("internal bug")))
    result_path = staged_bundle.bundle / LOCAL_RESULT_NAME
    with pytest.raises(RuntimeError, match="internal bug"):
        module.main(local_arguments(staged_bundle, result_path, None))
    assert not result_path.exists(), "a crashed run must write no completed result"


def test_local_result_uses_exact_documented_local_identity_values(
    staged_bundle: StagedBundle,
) -> None:
    """Local mode emits the exact documented non-uploadable identity values."""
    payload = completed_local_result(staged_bundle, staged_bundle.bundle / LOCAL_RESULT_NAME)
    wrong = [field for field, expected in LOCAL_IDENTITY.items() if payload.get(field) != expected]
    assert not wrong, f"Local identity fields must match SPEC.md exactly; wrong: {wrong}."
    datetime_value = payload.get("datetime")
    assert DATETIME_PATTERN.match(str(datetime_value)), (
        f"Local datetime must be current UTC in YYYY-MM-DDTHH:MM:SSZ form: {datetime_value!r}"
    )


def test_native_result_uses_canonical_field_names_without_old_aliases(
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The native payload uses schema/test-name/passed and no superseded aliases."""
    payload = _completed_native_result(staged_bundle, monkeypatch)
    assert_canonical_result_fields(payload, expected_row_names())


def test_local_result_uses_canonical_field_names_without_old_aliases(
    staged_bundle: StagedBundle,
) -> None:
    """The local payload uses schema/test-name/passed and no superseded aliases."""
    payload = completed_local_result(staged_bundle, staged_bundle.bundle / LOCAL_RESULT_NAME)
    assert_canonical_result_fields(payload, expected_row_names())


# ---------------------------------------------------------------------------
# Case 7: a passing call phase with a failing teardown is scored as failed.
# ---------------------------------------------------------------------------


def test_passing_call_with_failing_teardown_is_scored_as_failed(tmp_path: Path) -> None:
    """A teardown failure cannot be discarded in favour of an earlier call-phase pass.

    The score assertions come first and use field names that the superseded
    result shape also carries, so the only reason this can fail is the teardown
    outcome rule itself.
    """
    staged = stage_bundle(tmp_path, hidden_test_source=teardown_hidden_test_source())
    payload = completed_local_result(staged, staged.bundle / LOCAL_RESULT_NAME)
    assert payload["max-score"] == TEARDOWN_CASE_COUNT
    assert payload["score"] == 0, (
        "A test whose call phase passes but whose teardown fails must not score a point."
    )
    row = payload["tests"][0]
    assert row["max-score"] == TEARDOWN_CASE_COUNT
    assert row["score"] == 0
    assert row["passed"] is False, "The teardown failure must be reported as not passed."
    assert row["test-name"] == teardown_row_name()


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
    staged_bundle: StagedBundle, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The upstream runner sets OWNER and USERNAME to one repository identity."""
    env = native_environment(staged_bundle)
    assert env["GITHUB_REPOSITORY"] == GITHUB_REPOSITORY
    assert env["OWNER"] == env["USERNAME"] == NATIVE_OWNER
    payload = _completed_native_result(staged_bundle, monkeypatch)
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
    staged_bundle: StagedBundle,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    """Native grading preserves the individual/group/team identity from the environment."""
    payload = _completed_native_result(
        staged_bundle,
        monkeypatch,
        MODE=mode,
        ASSIGNMENT_TYPE=assignment_type_from_mode(mode),
    )
    assert payload.get("assignment_type") == mode
    assert_canonical_result_fields(payload, expected_row_names())
