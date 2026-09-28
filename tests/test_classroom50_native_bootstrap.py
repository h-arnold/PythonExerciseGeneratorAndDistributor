"""RED tests for the Stage 3 native dependency bootstrap and target contract.

``ACTION_PLAN.md`` Stage 3 makes native grading independent of the student
checkout's Python environment: the builder emits a committed, lock-parity-checked
``requirements.txt`` beside the other three target contract files, and the
bundle-local grader installs that file into a fresh bundle-local target before it
may import pytest.  This module is the red suite for that contract.

## The seam contract

``SPEC.md`` requires exactly this shape of test: "Repository tests must mock
package-version discovery, module-origin checks, and pip subprocesses; they must
not access the network."  ``scripts/autograder.py`` must therefore provide four
module-level callables - ``bootstrap_native_dependencies``,
``import_verified_pytest``, ``installed_distribution_version``, and
``installed_module_origin`` - and ``tests/_classroom50_bootstrap.py`` documents
their exact signatures, derives the expected pins from ``uv.lock`` rather than
restating them, and supplies the fakes.  A missing seam is reported as one sharp
red failure naming every missing callable, not as a collection-time
``ImportError``.

## Why native runs are in-process here

The repository virtual environment has no ``pip``, and the fixed argv Stage 3 pins
offers no offline switch: ``--isolated`` plus the mandatory ``PIP_*`` scrub rules
out ``PIP_NO_INDEX``/``PIP_FIND_LINKS``, and a monkeypatch cannot cross a process
boundary.  The native runs below therefore call ``main([])`` in-process with the
pip subprocess faked.  Real pytest still collects and runs the hidden tests; only
the operating-system process boundary is given up.  Native *failure* paths that
fail before the bootstrap - a missing identity variable, an unsupported
assignment type, an in-place script run - stay real child subprocesses in
``tests/test_classroom50_native_autograder.py``.

Two consequences of running in-process are handled explicitly here:

* the nested ``pytest.main`` must not discover this repository's broad root
  ``pytest.ini`` and ``conftest.py``, which a subprocess child launched from
  ``tmp_path`` would never see.  The staged bundle ships its own ``pytest.ini``,
  which stops the upward rootdir walk inside the bundle, and that ini requests a
  junit report with a relative path.  ``STAGED_INIFILE_PROOF`` is the file that
  proves which ini was in force.
* the outer session has already imported ``exercise_runtime_support`` and
  ``exercise_metadata``, so an in-process run would reuse the repository copies
  and fail the package-origin check for the wrong reason.
  ``isolate_bundle_imports`` gives the run a private module table, restored on
  teardown.

## Manifest scope

``grading_manifest.json`` emission is asserted in
``tests/test_classroom50_bundle_stage4.py``, which drives the real builder.  This
module only requires that the bundle carries one, because the bootstrap reads
``requirements.txt`` and the grader discovers hidden tests from the bundle.

The synthetic exercise key used by the staged bundle exists nowhere in the
repository, so no construct-specific or pilot-specific implementation branch can
satisfy these tests.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests._classroom50_bootstrap import (
    BUNDLE_PYTEST_INI_NAME,
    BUNDLE_PYTEST_INI_SOURCE,
    BUNDLE_REQUIREMENTS_NAME,
    FAKE_INSTALL_MARKER,
    MISMATCHED_VERSION,
    NATIVE_PIP_TIMEOUT_SECONDS,
    PIP_ENV_PREFIX,
    PIP_FLAG_ARGUMENTS,
    PYTEST_DISTRIBUTION,
    SEAM_BOOTSTRAP,
    SEAM_IMPORT_PYTEST,
    SEAM_INSTALLED_VERSION,
    SEAM_NAMES,
    BootstrapHarness,
    bundle_files,
    load_autograder_module,
    missing_seams,
    run_local_in_process,
    run_native_in_process,
    seam,
)
from tests._classroom50_lock import (
    WINDOWS_PLATFORM_MARKER,
    active_platform_pins,
    committed_requirements_bytes,
    lock_derived_requirements,
    locked_active_pins,
    locked_closure_pins,
    locked_markers,
    requirement_markers,
    requirement_pins,
    windows_active,
)
from tests._classroom50_source_scan import (
    BUNDLE_OWNED_IMPORTS,
    DEFERRED_THIRD_PARTY_IMPORTS,
    STUDENT_DEPENDENCY_MANIFESTS,
    UV_EXECUTABLES,
    calls_named,
    code_string_literals,
    imports_pytest,
    non_deferred_pytest_imports,
    non_stdlib_imports_in_function,
    non_stdlib_imports_in_functions,
    non_stdlib_module_imports,
    pytest_import_sites,
    third_party_runtime_imports,
)
from tests._classroom50_test_helpers import (
    EXERCISE_KEY,
    HIDDEN_TEST_FILENAME,
    LOCAL_RESULT_NAME,
    LOCAL_VARIANT,
    PASSING_CASE_COUNT,
    STAGED_INIFILE_PROOF,
    StagedBundle,
    autograder_source,
    expected_row_name,
    expected_row_names,
    local_arguments,
    passing_hidden_test_source,
    read_result,
    run_local_child,
    stage_bundle,
    write_stale_result,
)

STAGE3_REQUIREMENTS_TEXT = lock_derived_requirements()
STAGE3_ACTIVE_PINS = active_platform_pins(STAGE3_REQUIREMENTS_TEXT)
REQUIRED_DISTRIBUTIONS = tuple(sorted(STAGE3_ACTIVE_PINS))

# The documented requirements source transcribed from ``SPEC.md`` (section
# "Hidden-test manifest contract") and ``WORKFLOW_SPEC.md``.  This is a
# transcription of the documented block, so the ordering and exact spelling are
# pinned; ``test_the_committed_native_requirements_pins_match_the_uv_lock_closure``
# separately proves the pins against ``uv.lock`` itself.
DOCUMENTED_REQUIREMENTS_BLOCK = """pytest==9.0.2
tabulate==0.9.0
iniconfig==2.3.0
packaging==26.0
pluggy==1.6.0
pygments==2.19.2
colorama==0.4.6; sys_platform == "win32"
"""

# Inherited pip configuration that must not survive into the fixed invocation.
HOSTILE_PIP_ENVIRONMENT = {
    "PIP_TARGET": "/tmp/stage3-hostile-target",
    "PIP_INDEX_URL": "https://packages.invalid/simple",
    "PIP_EXTRA_INDEX_URL": "https://mirror.invalid/simple",
    "PIP_FIND_LINKS": "https://packages.invalid/wheels",
    "PIP_USER": "1",
    "PIP_CONFIG_FILE": "/tmp/stage3-hostile-pip.conf",
    "PIP_REQUIRE_VIRTUALENV": "true",
    "PIP_NO_INDEX": "1",
}

# A hidden module whose collected cases all fail, so a completed native run can be
# told apart from an infrastructure failure.
FAILING_HIDDEN_TEST = '''"""Synthetic hidden test module whose cases fail in every variant."""

import pytest


@pytest.mark.parametrize("case", ["alpha", "beta"])
def test_native_bundle_failure(case):
    assert False, f"case {case} was not implemented"
'''

FAILING_ROW_NAMES = [
    expected_row_name(EXERCISE_KEY, f"{HIDDEN_TEST_FILENAME}::test_native_bundle_failure[{case}]")
    for case in ("alpha", "beta")
]

# A synthetic hidden module that uses the repository's exercise task marker, so the
# bundle configuration's ``markers`` entry has a runtime effect to observe.
TASK_MARKER_HIDDEN_TEST = '''"""Synthetic hidden test module that uses the exercise task marker."""

import pytest


@pytest.mark.task(taskno=1)
def test_task_marker_case():
    assert True
'''

# A bundle configuration that declares no marker at all, so the same hidden module
# produces the unknown-mark warning the committed file exists to prevent.
MARKERLESS_INI = "[pytest]\n"


def _committed_requirements_text() -> str:
    """Return the committed native requirements source as text."""
    return committed_requirements_bytes().decode("utf-8")


def _parsed_requirements(tmp_path: Path, text: str) -> list[tuple[str, str]]:
    """Return the ``(distribution, version)`` pins the bootstrap reads from ``text``.

    The requirement parser has no seam - it is an internal step of the bootstrap -
    so it is reached through the module object, as ``tests/test_new_exercise.py``
    reaches the other private script helpers.
    """
    requirements = tmp_path / BUNDLE_REQUIREMENTS_NAME
    requirements.write_text(text, encoding="utf-8")
    parse = load_autograder_module()._required_packages
    return [(pin.distribution, pin.version) for pin in parse(requirements)]


def _expected_pip_argv(target: Path, requirements: Path) -> list[str]:
    """Return the documented pip argument vector for a fresh ``target``."""
    return [
        sys.executable,
        "-m",
        "pip",
        *PIP_FLAG_ARGUMENTS,
        "--target",
        str(target),
        "-r",
        str(requirements),
    ]


def _stage_bootstrap_bundle(
    tmp_path: Path, *, hidden_test_source: str | None = None
) -> StagedBundle:
    """Stage a bundle whose requirements source is the locked native closure.

    The committed source is asserted separately; the fixture is rendered from
    ``uv.lock`` so the bootstrap tests fail for the missing bootstrap rather than
    for a missing committed file.
    """
    return stage_bundle(
        tmp_path,
        hidden_test_source=hidden_test_source or passing_hidden_test_source(),
        requirements_text=STAGE3_REQUIREMENTS_TEXT,
    )


def _patched_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
    **harness_options: Any,
) -> tuple[BootstrapHarness, Callable[..., Any], ModuleType]:
    """Install the fake install fakes and return them with the bootstrap seam.

    ``sys.path`` is snapshotted so a bootstrap that prepends its fresh target
    cannot leak that path into the running test session.
    """
    module = load_autograder_module()
    harness = BootstrapHarness(**harness_options).with_installed_pins(STAGE3_ACTIVE_PINS)
    harness.patch(monkeypatch, module)
    monkeypatch.setattr(sys, "path", list(sys.path))
    return harness, seam(module, SEAM_BOOTSTRAP), module


# ---------------------------------------------------------------------------
# The lock-derived native dependency source.
# ---------------------------------------------------------------------------


def test_the_committed_native_requirements_pins_match_the_uv_lock_closure() -> None:
    """Every committed pin is confirmed against ``uv.lock`` and the platform marker.

    The expected values are derived from the lockfile - the pytest closure plus
    the runtime's direct requirement - so this is a real parity check rather than
    a comparison of one hardcoded copy of the pins with another.  Three claims are
    made: the pinned set is exactly the locked closure, each locked platform marker
    survives, and the actively required subset is exactly the locked subset.
    """
    text = _committed_requirements_text()
    assert requirement_pins(text) == locked_closure_pins(), (
        "scripts/classroom50_requirements.txt must pin exactly the uv.lock closure."
    )
    assert requirement_markers(text) == locked_markers(), (
        "Each committed requirement must keep the platform marker uv.lock records."
    )
    assert active_platform_pins(text) == locked_active_pins(), (
        "The actively required subset must match the lockfile for this platform."
    )


def test_the_committed_native_requirements_mark_colorama_for_windows_only() -> None:
    """``colorama`` is required on Windows and is not required on other platforms.

    ``SPEC.md``: "``colorama`` is required on Windows and must not be required or
    installed on Linux."  The expectation is derived from the active platform
    marker, so the test states the same rule on every platform.
    """
    text = _committed_requirements_text()
    markers = requirement_markers(text)
    assert set(markers) == set(locked_markers()), (
        f"Only lockfile-marked requirements may carry a marker; found {sorted(markers)}."
    )
    assert markers.get("colorama") == WINDOWS_PLATFORM_MARKER, (
        "The Windows-only requirement must carry the lockfile's win32 marker."
    )
    assert ("colorama" in active_platform_pins(text)) is windows_active(), (
        "colorama must be required exactly on the platform its marker selects."
    )


def test_the_committed_native_requirements_match_the_documented_block() -> None:
    """The committed source is the exact block ``SPEC.md`` documents.

    This transcribes the documented block, so the line order and spelling are
    pinned here; the pins themselves are proven against ``uv.lock`` by
    ``test_the_committed_native_requirements_pins_match_the_uv_lock_closure``.
    """
    assert _committed_requirements_text() == DOCUMENTED_REQUIREMENTS_BLOCK


def test_the_lock_closure_covers_every_third_party_runtime_import() -> None:
    """Every non-stdlib runtime import must be inside the native requirement set.

    The bundle ships its own ``exercise_runtime_support`` copy, so the closure has
    to cover what that copy actually imports; this is why ``tabulate`` is a direct
    requirement rather than a pytest dependency.
    """
    runtime_imports = third_party_runtime_imports()
    assert runtime_imports, "The runtime must import at least pytest; the scan found none."
    missing = sorted(runtime_imports - set(active_platform_pins(_committed_requirements_text())))
    assert not missing, f"The native requirements source must cover {missing}."


def test_the_committed_requirements_source_parses_with_the_bootstrap_grammar(
    tmp_path: Path,
) -> None:
    """The bootstrap's own parser agrees with ``packaging`` about the committed source.

    The bootstrap cannot use ``packaging`` before the verified target exists, so it
    parses the closed grammar itself.  This states that the two readings of the
    committed file are the same active pin set, which is what makes the bootstrap's
    own reading trustworthy.  The comparison is order-free because the documented
    line order is pinned separately.
    """
    text = _committed_requirements_text()
    assert sorted(_parsed_requirements(tmp_path, text)) == sorted(
        active_platform_pins(text).items()
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("pytest==9.0.2\n", [("pytest", "9.0.2")]),
        ("# a whole-line comment\n\npytest==9.0.2\n", [("pytest", "9.0.2")]),
        ('colorama==0.4.6; sys_platform == "{platform}"\n', [("colorama", "0.4.6")]),
        ("colorama==0.4.6; sys_platform == '{platform}'\n", [("colorama", "0.4.6")]),
        ('colorama==0.4.6 ; sys_platform == "{platform}"\n', [("colorama", "0.4.6")]),
        ('colorama==0.4.6; sys_platform == "plan9"\n', []),
    ],
    ids=(
        "plain-pin",
        "comment-and-blank-line",
        "matching-marker",
        "single-quoted-marker",
        "space-before-separator",
        "other-platform",
    ),
)
def test_the_requirements_grammar_accepts_exact_pins_and_platform_markers(
    tmp_path: Path, text: str, expected: list[tuple[str, str]]
) -> None:
    """An exact pin is required, and a marker selects one platform or the other.

    The marker is compared against ``sys.platform`` - what ``packaging``'s
    ``sys_platform`` defaults to - so the expectation states the documented rule on
    every platform instead of assuming Linux.
    """
    assert _parsed_requirements(tmp_path, text.format(platform=sys.platform)) == expected


@pytest.mark.parametrize(
    "text",
    [
        "pytest",
        "pytest >= 9.0.2",
        "pytest[foo]==9.0.2",
        "pytest==9.0.2.*",
        "pytest==9.0.2 --hash=sha256:0",
        "pytest==9.0.2  # the pinned version",
        'pytest==9.0.2; python_version < "3.14"',
        'pytest==9.0.2; extra == "x"',
        'pytest==9.0.2; sys_platform >= "win32"',
    ],
    ids=(
        "unpinned",
        "range",
        "extras",
        "wildcard",
        "hash",
        "inline-comment",
        "other-marker",
        "extra-marker",
        "marker-operator",
    ),
)
def test_the_requirements_grammar_rejects_anything_outside_the_closed_grammar(
    tmp_path: Path, text: str
) -> None:
    """A range, extras, a wildcard, a hash, a comment, or another marker fails loudly.

    The requirements source is a set of exact pins, so anything else is a contract
    violation that would change what the native target receives; it is rejected
    rather than passed to pip to interpret.
    """
    with pytest.raises(RuntimeError, match="exact 'name==version' pin"):
        _parsed_requirements(tmp_path, f"{text}\n")


# ---------------------------------------------------------------------------
# The bootstrap seam and the fixed pip invocation.
# ---------------------------------------------------------------------------


def test_the_autograder_exposes_the_documented_dependency_bootstrap_seams() -> None:
    """Every locked Stage 3 seam exists on ``scripts/autograder.py``."""
    module = load_autograder_module()
    assert missing_seams(module) == [], (
        f"scripts/autograder.py must provide {SEAM_NAMES}; the contract is "
        "documented in tests/_classroom50_bootstrap.py."
    )


def test_native_bootstrap_uses_the_fixed_isolated_pip_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The install is exactly the documented argv with the documented timeout."""
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    target = bootstrap(staged.bundle)
    requirements = staged.bundle / BUNDLE_REQUIREMENTS_NAME
    assert target == harness.target
    assert harness.invocation.argv == _expected_pip_argv(target, requirements), (
        "The native install must use the fixed isolated pip invocation."
    )
    assert harness.invocation.timeout == NATIVE_PIP_TIMEOUT_SECONDS, (
        "The native install must be bounded by the documented 120-second timeout."
    )


def test_native_bootstrap_scrubs_every_inherited_pip_variable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hostile inherited pip environment cannot reach or redirect the install."""
    staged = _stage_bootstrap_bundle(tmp_path)
    for key, value in HOSTILE_PIP_ENVIRONMENT.items():
        monkeypatch.setenv(key, value)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    target = bootstrap(staged.bundle)
    inherited = sorted(key for key in harness.pip_environment if key.startswith(PIP_ENV_PREFIX))
    assert inherited == [], f"Inherited {PIP_ENV_PREFIX}* keys must be removed: {inherited}."
    assert "PATH" in harness.pip_environment, (
        "Only the pip variables are scrubbed; the rest of the environment is inherited."
    )
    hostile_target = HOSTILE_PIP_ENVIRONMENT["PIP_TARGET"]
    assert hostile_target not in harness.invocation.argv, (
        "A hostile PIP_TARGET must never become the install target."
    )
    assert target.is_relative_to(staged.bundle), (
        "The verified target must be bundle-local, never the redirected directory."
    )


def test_native_bootstrap_installs_into_a_fresh_bundle_local_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The target is a newly created directory beneath the bundle, not the checkout."""
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    target = bootstrap(staged.bundle)
    assert target.is_dir()
    assert target != staged.bundle, "The bundle root itself must not be the install target."
    assert target.is_relative_to(staged.bundle), f"{target} must live beneath the bundle."
    assert not target.is_relative_to(staged.student), (
        f"{target} must never be populated from or inside the student checkout."
    )
    assert not target.is_relative_to(Path(sys.prefix)), (
        f"{target} must never reuse the grading interpreter's own site-packages."
    )
    assert harness.requirements_argument == str(staged.bundle / BUNDLE_REQUIREMENTS_NAME), (
        "The bundle's own requirements file is the only install source."
    )


def test_native_bootstrap_recreates_the_target_on_every_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second run removes the previous target instead of installing into it."""
    staged = _stage_bootstrap_bundle(tmp_path)
    _, bootstrap, _ = _patched_bootstrap(monkeypatch)
    first = bootstrap(staged.bundle)
    planted = first / "planted-by-a-previous-run.py"
    planted.write_text("LEFTOVER = True\n", encoding="utf-8")
    second = bootstrap(staged.bundle)
    assert second == first, "The fresh bundle-local target must be a stable location."
    assert not planted.exists(), "The previous target contents must be removed, not reused."
    assert (second / FAKE_INSTALL_MARKER).is_file(), (
        "The recreated target must hold the newly installed packages."
    )


def test_native_bootstrap_verifies_every_required_version_under_the_fresh_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every actively required package is version-checked, and under the target.

    The harness refuses a lookup scoped to any other directory, so a globally
    scoped implementation - which ``SPEC.md`` forbids - cannot pass here.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    target = bootstrap(staged.bundle)
    assert sorted(harness.version_requests) == list(REQUIRED_DISTRIBUTIONS), (
        "Every actively required distribution must be version-checked."
    )
    assert {scoped for _, scoped in harness.version_lookups} == {target}, (
        "Every version must be read under the fresh target, never the global environment."
    )


def test_native_bootstrap_verifies_every_required_module_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every actively required package is origin-checked under the fresh target.

    Origin checks may name the module a distribution resolves through rather than
    the distribution itself, so the claim is a count plus the pytest origin, not
    name identity between the two sets.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    target = bootstrap(staged.bundle)
    assert len(harness.origin_modules) >= len(REQUIRED_DISTRIBUTIONS), (
        f"Each required package needs its own origin check; read {sorted(harness.origin_modules)}."
    )
    assert PYTEST_DISTRIBUTION in harness.origin_modules, (
        "pytest itself must be origin-checked before it is imported."
    )
    assert {scoped for _, scoped in harness.origin_lookups} == {target}, (
        "Every origin must be checked under the fresh target."
    )


def test_native_bootstrap_requires_colorama_only_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``colorama`` is not required or verified away from Windows.

    The expectation comes from the active platform marker, so this states the
    documented rule on Windows and on every other platform alike.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    bootstrap(staged.bundle)
    assert ("colorama" in harness.version_requests) is windows_active(), (
        "colorama must only be required on the platform its marker selects."
    )
    assert ("colorama" in harness.origin_modules) is windows_active(), (
        "colorama must only be origin-checked on the platform its marker selects."
    )


def test_native_bootstrap_prepends_the_verified_target_ahead_of_the_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The verified target is prepended ahead of the bundle and the checkout.

    ``ACTION_PLAN.md`` Stage 2 records the required order: the verified fresh
    target, then the bundle root, then the student checkout.  The bundle and
    checkout are already ahead of everything else when the bootstrap runs, so
    prepending the target completes that order.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    _, bootstrap, _ = _patched_bootstrap(monkeypatch)
    monkeypatch.setattr(sys, "path", [str(staged.bundle), str(staged.student), *sys.path])
    target = bootstrap(staged.bundle)
    assert sys.path[:3] == [str(target), str(staged.bundle), str(staged.student)], (
        "The verified target must be prepended without disturbing the bundle/checkout order."
    )
    assert sys.path.count(str(target)) == 1


def test_configuring_bundle_paths_keeps_an_already_verified_target_in_front(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bundle/checkout pair cannot be pushed in front of a verified target.

    The bootstrap owns the first entry of the documented ``sys.path`` order and
    ``configure_bundle_paths`` owns the next two.  Every later stage edits this file,
    so re-ordering the pair after a bootstrap has to leave the target ahead of it
    rather than displacing it.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    module = load_autograder_module()
    _, bootstrap, _ = _patched_bootstrap(monkeypatch)
    target = bootstrap(staged.bundle)
    module.configure_bundle_paths(staged.bundle, staged.student)
    assert sys.path[:3] == [str(target), str(staged.bundle), str(staged.student)], (
        "The verified target must stay ahead of the bundle root and the student checkout."
    )
    assert sys.path.count(str(target)) == 1


# ---------------------------------------------------------------------------
# Dependency failures are infrastructure failures.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("returncode", "stderr"),
    [
        (1, "ERROR: No module named pip"),
        (2, "ERROR: Could not install packages due to an OSError"),
    ],
    ids=("pip-missing", "install-failed"),
)
def test_native_bootstrap_fails_when_pip_reports_a_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stderr: str,
) -> None:
    """A missing or failing pip is an infrastructure failure, not a graded run."""
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(
        monkeypatch, pip_returncode=returncode, pip_stderr=stderr
    )
    with pytest.raises(RuntimeError):
        bootstrap(staged.bundle)
    assert len(harness.invocations) == 1, "The fixed pip invocation must still be attempted."


def test_native_bootstrap_fails_when_the_install_times_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pip timeout is converted into the module's infrastructure failure."""
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(
        monkeypatch,
        pip_exception=subprocess.TimeoutExpired(
            cmd=[sys.executable, "-m", "pip"], timeout=NATIVE_PIP_TIMEOUT_SECONDS
        ),
    )
    with pytest.raises(RuntimeError):
        bootstrap(staged.bundle)
    assert harness.invocations[0].timeout == NATIVE_PIP_TIMEOUT_SECONDS


@pytest.mark.parametrize("distribution", REQUIRED_DISTRIBUTIONS, ids=REQUIRED_DISTRIBUTIONS)
def test_native_bootstrap_fails_when_a_required_package_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, distribution: str
) -> None:
    """An incomplete target is an infrastructure failure for every required package."""
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    harness.absent_distributions.add(distribution)
    with pytest.raises(RuntimeError):
        bootstrap(staged.bundle)
    assert distribution in harness.version_requests


@pytest.mark.parametrize("distribution", REQUIRED_DISTRIBUTIONS, ids=REQUIRED_DISTRIBUTIONS)
def test_native_bootstrap_fails_on_an_installed_version_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, distribution: str
) -> None:
    """A wrong installed version is rejected for every required package."""
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    harness.installed_versions[distribution] = MISMATCHED_VERSION
    with pytest.raises(RuntimeError):
        bootstrap(staged.bundle)
    assert distribution in harness.version_requests


@pytest.mark.parametrize("distribution", REQUIRED_DISTRIBUTIONS, ids=REQUIRED_DISTRIBUTIONS)
def test_native_bootstrap_fails_on_a_module_origin_outside_the_fresh_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, distribution: str
) -> None:
    """A module resolving outside the fresh target is rejected for every package."""
    staged = _stage_bootstrap_bundle(tmp_path)
    harness, bootstrap, _ = _patched_bootstrap(monkeypatch)
    harness.foreign_origin_distributions.add(distribution)
    with pytest.raises(RuntimeError):
        bootstrap(staged.bundle)
    assert distribution in harness.origin_modules


def test_native_bootstrap_removes_the_fresh_target_when_it_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed bootstrap cleans the fresh target up instead of leaving it behind.

    ``SPEC.md``: the target is "cleaned up on failure".  An empty runtime parent
    directory is acceptable, but no partially installed target content may
    survive to be picked up by a later run.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    before = bundle_files(staged.bundle)
    harness, bootstrap, _ = _patched_bootstrap(
        monkeypatch, pip_returncode=1, pip_stderr="ERROR: No module named pip"
    )
    with pytest.raises(RuntimeError):
        bootstrap(staged.bundle)
    assert harness.target is not None, "The fixed invocation must have named a fresh target."
    assert not harness.target.exists(), f"{harness.target} must be removed after a failure."
    leaked = sorted(bundle_files(staged.bundle) - before)
    assert not leaked, f"A failed bootstrap must not leave installed files behind: {leaked}."


def test_native_bootstrap_removes_the_target_when_verification_raises_unexpectedly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A verification hook raising something undeclared still leaves no target behind.

    ``installed_distribution_version`` and ``installed_module_origin`` read an
    arbitrary installed tree, so a corrupt ``.dist-info`` can surface as an ``OSError``
    or a parse ``ValueError`` rather than the declared failure type. ``SPEC.md``
    requires the target to be "cleaned up on failure" however the failure surfaced,
    and the exception has to reach the caller unchanged rather than be swallowed.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    before = bundle_files(staged.bundle)
    harness, bootstrap, module = _patched_bootstrap(monkeypatch)

    def _corrupt_metadata(distribution: str, *, target: Path) -> str:
        """Stand in for a version hook that cannot read a corrupt installed tree."""
        raise ValueError(f"corrupt metadata for {distribution}")

    monkeypatch.setattr(module, SEAM_INSTALLED_VERSION, _corrupt_metadata)
    with pytest.raises(ValueError, match="corrupt metadata for"):
        bootstrap(staged.bundle)
    assert harness.target is not None, "The fixed invocation must have named a fresh target."
    assert not harness.target.exists(), f"{harness.target} must be removed after a failure."
    leaked = sorted(bundle_files(staged.bundle) - before)
    assert not leaked, f"A failed bootstrap must not leave installed files behind: {leaked}."


def test_a_dependency_bootstrap_failure_writes_no_result_and_exits_non_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A child whose bootstrap fails is an infrastructure failure at the child boundary.

    The recorded invocation is asserted alongside the exit status, because an
    unhandled ``RuntimeError`` also maps to a non-zero exit: without the argv
    assertion this test could pass for a package-origin or identity failure that
    never reached the install.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    write_stale_result(staged.result_path)
    run = run_native_in_process(
        monkeypatch, staged, pip_returncode=1, pip_stderr="ERROR: No module named pip"
    )
    assert run.harness.target is not None, "the failing run must have named a fresh target"
    assert run.harness.invocations, "the native run must have attempted the fixed install"
    assert run.harness.invocation.argv == _expected_pip_argv(
        run.harness.target, staged.bundle / BUNDLE_REQUIREMENTS_NAME
    ), "the failing install must be the documented fixed invocation"
    assert run.exit_code != 0, (
        "A dependency bootstrap failure must end the child with a non-zero exit."
    )
    assert not staged.result_path.exists(), (
        "A stale child result must not survive a dependency bootstrap failure."
    )


# ---------------------------------------------------------------------------
# The Stage 3 positive: a successful bootstrap grades the checkout and exits zero.
# ---------------------------------------------------------------------------


def test_a_successful_bootstrap_grades_the_checkout_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A verified bootstrap leads to the canonical result and a completed exit 0.

    This is ``ACTION_PLAN.md`` Stage 3's "A completed pass/fail still writes the
    canonical result and exits 0" for the native path: the run installed the pinned
    closure into a fresh target, verified every version and origin under it, and
    only then graded the checkout.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    run = run_native_in_process(monkeypatch, staged)
    harness = run.harness
    assert harness.target is not None, "a successful native run must have installed a target"
    assert harness.invocation.argv == _expected_pip_argv(
        harness.target, staged.bundle / BUNDLE_REQUIREMENTS_NAME
    )
    assert sorted(harness.version_requests) == list(REQUIRED_DISTRIBUTIONS)
    assert len(harness.origin_modules) >= len(REQUIRED_DISTRIBUTIONS)
    assert harness.target.is_relative_to(staged.bundle)
    ordered = [str(harness.target), str(staged.bundle), str(staged.student)]
    positions = [sys.path.index(entry) for entry in ordered]
    assert positions == sorted(positions), (
        "the verified target, the bundle, and the student checkout must all be on "
        f"sys.path in that order; got {sys.path[:6]}"
    )
    assert run.exit_code == 0, f"a completed native run must exit 0, not {run.exit_code}"
    payload = read_result(staged.result_path)
    assert payload["score"] == PASSING_CASE_COUNT
    assert [row["test-name"] for row in payload["tests"]] == expected_row_names()
    assert (staged.student / STAGED_INIFILE_PROOF).is_file(), (
        "the staged bundle pytest.ini must govern the in-process run, so its junit "
        f"report lands in the run's working directory; missing {STAGED_INIFILE_PROOF}"
    )


def test_a_completed_native_run_whose_cases_fail_still_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failing collected cases are a completed run: zero score, canonical result, exit 0.

    ``SPEC.md`` reserves a non-zero exit for infrastructure failures only, so a
    student who has implemented nothing is graded, not crashed.
    """
    staged = _stage_bootstrap_bundle(tmp_path, hidden_test_source=FAILING_HIDDEN_TEST)
    run = run_native_in_process(monkeypatch, staged)
    assert run.harness.version_requests, "a completed native run must verify its dependencies"
    assert run.exit_code == 0, f"collected failures must still exit 0, not {run.exit_code}"
    payload = read_result(staged.result_path)
    assert payload["max-score"] == PASSING_CASE_COUNT
    assert payload["score"] == 0
    assert [row["test-name"] for row in payload["tests"]] == FAILING_ROW_NAMES
    assert all(row["passed"] is False for row in payload["tests"])


def test_a_local_dry_run_never_bootstraps_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Local mode grades from the developer's environment and installs nothing.

    ``SPEC.md`` scopes the fresh target to native mode, and a local run that
    installed would make the offline dry-run workflow depend on a package index.
    Every subprocess entry point and every installed seam is replaced with a
    recorder that fails, so a bootstrapping local run fails loudly here.
    """
    module = load_autograder_module()
    assert missing_seams(module) == [], (
        f"scripts/autograder.py must provide {SEAM_NAMES}; a local run can only stay "
        "offline once the seams exist to be bypassed."
    )
    staged = _stage_bootstrap_bundle(tmp_path)
    result_path = staged.bundle / LOCAL_RESULT_NAME
    run = run_local_in_process(monkeypatch, staged, result_path)
    assert run.bootstrap_calls == 0, "a local dry run must not call the bootstrap seam"
    assert run.subprocess_calls == [], "a local dry run must not launch a subprocess"
    assert run.seam_calls == [], "a local dry run must not call the verification seams"
    assert run.exit_code == 0, f"a local dry run must still grade the checkout, not {run.exit_code}"
    payload = read_result(result_path)
    assert payload["score"] == PASSING_CASE_COUNT
    assert payload["owner"] == "local"


def test_a_local_child_run_never_creates_the_native_install_target(tmp_path: Path) -> None:
    """A local dry-run *child* installs nothing either, so no target appears.

    The in-process run above proves the seams are bypassed; this proves the same for
    the subprocess path, which has no monkeypatch to fall back on.  The bundle carries
    real lock-derived pins, so a local run that bootstrapped would get past the
    requirements grammar and reach a real ``pip install`` on any machine whose
    interpreter has pip.  The absent target is asserted first, because it names the
    regression even when the ensuing install failure also breaks the exit code.
    """
    staged = _stage_bootstrap_bundle(tmp_path)
    result_path = staged.bundle / LOCAL_RESULT_NAME
    proc = run_local_child(staged, *local_arguments(staged, result_path, LOCAL_VARIANT))
    runtime_root = staged.bundle / load_autograder_module().NATIVE_RUNTIME_DIRNAME
    assert not runtime_root.exists(), (
        f"a local dry run must never create the native install target {runtime_root}"
    )
    assert proc.returncode == 0, f"a local dry run must still grade the checkout.\n{proc.stderr}"
    assert read_result(result_path)["owner"] == "local"


# ---------------------------------------------------------------------------
# The committed bundle pytest configuration.
# ---------------------------------------------------------------------------


def _stage_bundle_with_inifile(tmp_path: Path, ini_text: str) -> StagedBundle:
    """Stage a bundle whose pytest configuration is exactly ``ini_text``.

    ``stage_bundle`` ships a placeholder ini, so the committed file's own runtime
    effect is only observable once that placeholder is replaced.
    """
    staged = stage_bundle(tmp_path, hidden_test_source=TASK_MARKER_HIDDEN_TEST)
    (staged.bundle / BUNDLE_PYTEST_INI_NAME).write_text(ini_text, encoding="utf-8")
    return staged


@pytest.mark.parametrize(
    ("ini_text", "expects_unknown_mark_warning"),
    [
        pytest.param(BUNDLE_PYTEST_INI_SOURCE.read_text(encoding="utf-8"), False, id="committed"),
        pytest.param(MARKERLESS_INI, True, id="markers-absent"),
    ],
)
def test_the_committed_bundle_configuration_registers_the_task_marker(
    tmp_path: Path, ini_text: str, expects_unknown_mark_warning: bool
) -> None:
    """The committed ini's ``markers`` entry is a runtime effect, not decoration.

    ``scripts/classroom50_pytest.ini`` is the bundle's trusted configuration, and the
    bundled hidden test modules do use ``pytest.mark.task``.  The byte-for-byte copy
    test only proves the file was transmitted; this proves it changed the run, by
    reading the child run's own warnings summary rather than by suppressing the
    warning anywhere.  The summary lands on the child's stdout, so both streams are
    read.
    """
    staged = _stage_bundle_with_inifile(tmp_path, ini_text)
    result_path = staged.bundle / LOCAL_RESULT_NAME
    proc = run_local_child(staged, *local_arguments(staged, result_path, LOCAL_VARIANT))
    diagnostics = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, f"the local child must complete.\n{diagnostics}"
    assert ("PytestUnknownMarkWarning" in diagnostics) is expects_unknown_mark_warning, (
        "the committed configuration must register the task marker, and a configuration "
        f"without it must let the warning through.\n{diagnostics}"
    )


# ---------------------------------------------------------------------------
# The deferred pytest import, the standard-library-only bootstrap, and the
# forbidden dependency sources.
# ---------------------------------------------------------------------------


def test_every_pytest_import_is_deferred_into_a_function_body() -> None:
    """No pytest import may run while the module is imported.

    ``SPEC.md`` requires the import to be deferred "until after the fresh target
    has been installed, version-checked, origin-checked, and prepended to
    ``sys.path``", so a module-scope, class-body, or conditionally executed import
    would reach the student's or the global pytest instead.  A ``TYPE_CHECKING``
    import is deferred by construction because it never executes.
    """
    offenders = non_deferred_pytest_imports(autograder_source())
    assert offenders == [], (
        f"scripts/autograder.py must defer every pytest import into a function body: {offenders}."
    )


def test_the_verified_target_importer_bootstraps_before_importing_pytest() -> None:
    """The verified-target importer installs and verifies before it imports pytest.

    Together with the runtime ``sys.path`` prepend assertion and the child-level
    failure test, this is what ties the native import to the fresh target: a native
    run that skipped the bootstrap would fail the child-level test, and an import
    that happened first would fail this one.
    """
    sites = pytest_import_sites(autograder_source())
    assert SEAM_IMPORT_PYTEST in sites, (
        f"{SEAM_IMPORT_PYTEST}() must import pytest; found {sorted(sites)}."
    )
    body = sites[SEAM_IMPORT_PYTEST]
    bootstrap_steps = [
        index for index, step in enumerate(body) if calls_named(step, SEAM_BOOTSTRAP)
    ]
    import_steps = [index for index, step in enumerate(body) if imports_pytest(step)]
    assert bootstrap_steps, f"{SEAM_IMPORT_PYTEST}() must call {SEAM_BOOTSTRAP}()."
    assert import_steps, f"{SEAM_IMPORT_PYTEST}() must import pytest."
    assert min(bootstrap_steps) < min(import_steps), (
        f"{SEAM_IMPORT_PYTEST}() must prepend the verified target before importing pytest."
    )


def test_the_autograder_imports_only_bundle_owned_modules_at_module_level() -> None:
    """No installed package may be imported while the module is imported.

    The bootstrap runs before the verified target exists, so a module-scope
    ``import packaging`` (or anything else outside the standard library and the
    bundle's own modules) would read the student or global environment - the very
    leak Stage 3 exists to close.  ``python -S`` shows ``packaging`` is not even
    importable without the target.
    """
    forbidden = {
        name: lines
        for name, lines in non_stdlib_module_imports(autograder_source()).items()
        if name not in BUNDLE_OWNED_IMPORTS
    }
    assert not forbidden, (
        "scripts/autograder.py must import only the standard library and the bundle's "
        f"own modules at module load; found {forbidden}."
    )


def test_the_bootstrap_path_imports_nothing_third_party() -> None:
    """The fresh-target lifecycle must not import an installed package either.

    The bootstrap parses the requirements, installs, and verifies all before the
    target is on ``sys.path``, so it has to work on the standard library alone.
    """
    bootstrap_imports = non_stdlib_imports_in_function(autograder_source(), SEAM_BOOTSTRAP)
    assert not bootstrap_imports, (
        f"{SEAM_BOOTSTRAP}() must import nothing outside the standard library and the "
        f"bundle's own modules; found {bootstrap_imports}."
    )
    importer_imports = {
        name: lines
        for name, lines in non_stdlib_imports_in_function(
            autograder_source(), SEAM_IMPORT_PYTEST
        ).items()
        if name not in BUNDLE_OWNED_IMPORTS | DEFERRED_THIRD_PARTY_IMPORTS
    }
    assert not importer_imports, (
        f"{SEAM_IMPORT_PYTEST}() may only import the standard library, the bundle's own "
        f"modules, and the deferred pytest; found {importer_imports}."
    )
    elsewhere = {
        name: lines
        for name, lines in non_stdlib_imports_in_functions(autograder_source()).items()
        if name not in BUNDLE_OWNED_IMPORTS | DEFERRED_THIRD_PARTY_IMPORTS
    }
    assert not elsewhere, (
        "no function may import an installed package before the verified target "
        f"exists, not even through a helper; found {elsewhere}."
    )


def test_native_grading_never_invokes_uv() -> None:
    """Native runtime code installs with ``sys.executable -m pip``, never with uv."""
    invoked = sorted(
        {value for value in code_string_literals(autograder_source()) if value in UV_EXECUTABLES}
    )
    assert invoked == [], (
        f"scripts/autograder.py must not run {invoked}; the native install uses "
        "sys.executable -m pip."
    )


def test_native_grading_never_reads_the_student_dependency_manifest() -> None:
    """No student dependency manifest may be read to decide what to install."""
    read = sorted(
        {
            value
            for value in code_string_literals(autograder_source())
            if any(
                value == name or value.endswith(f"/{name}") for name in STUDENT_DEPENDENCY_MANIFESTS
            )
        }
    )
    assert read == [], (
        f"scripts/autograder.py must install from the bundle requirements file only; "
        f"it refers to {read}."
    )
