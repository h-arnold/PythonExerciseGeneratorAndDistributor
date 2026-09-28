"""Test harness for the Stage 3 native dependency bootstrap and lock parity.

``ACTION_PLAN.md`` Stage 3 requires native grading to be independent of the student
checkout's Python environment: the builder will emit a lock-parity-checked
requirements file, and the bundle-local grader must install it into a fresh
bundle-local target before it may import pytest.  ``SPEC.md`` requires the
repository tests for that bootstrap to "mock package-version discovery,
module-origin checks, and pip subprocesses; they must not access the network",
so this module is the network-free side of that contract: it fakes the pip
subprocess and the two verification hooks, and drives the grader's own entry
point in-process.

The contract is split across three support modules, and this one stays with the
harness because the harness is the contract's other half:

* ``tests/_classroom50_lock.py`` derives the expected pins from ``uv.lock`` and
  parses a requirements file into pins and platform markers.
* ``tests/_classroom50_source_scan.py`` answers the structural questions about
  ``scripts/autograder.py``'s source: where each import executes, which installed
  packages it reaches for, and whether a statement calls a given callable.
* this module owns the fakes, the seam lookup, and the in-process run drivers.

## Seam contract locked by these tests

``scripts/autograder.py`` must provide the following module-level callables.
Nothing else about the implementation is pinned, and the bundle-local grader is
free to organise the surrounding code however it likes:

``bootstrap_native_dependencies(bundle_root: Path) -> Path``
    Remove and recreate a fresh target beneath the bundle, run the fixed
    isolated pip invocation against ``<bundle_root>/requirements.txt`` with a
    120-second timeout and no inherited ``PIP_*`` key, verify every actively
    required version and module origin under that target, prepend the verified
    target to ``sys.path``, and return it.  Every infrastructure failure (missing
    or failing pip, timeout, incomplete target, wrong version, wrong origin)
    raises a ``RuntimeError`` subclass and removes the fresh target.

    The install must be launched with ``subprocess.run(argv, env=..., timeout=...)``:
    the harness replaces ``subprocess.run`` and additionally replaces
    ``subprocess.Popen``, ``check_call``, and ``check_output`` with recorders that
    fail loudly, so a ``Popen``-based implementation cannot escape the fake and
    perform a real network install.

``import_verified_pytest(bundle_root: Path) -> ModuleType``
    The native pytest entry point.  It calls ``bootstrap_native_dependencies``
    first and imports pytest only afterwards, returning the imported module.  A
    local dry run is a developer-environment dry run and may import its own
    interpreter's pytest; every ``import pytest`` still has to sit inside a
    function body, because no import may run at module load.

``installed_distribution_version(distribution: str, *, target: Path) -> str``
    Package-version discovery hook, scoped to the fresh target.  The keyword-only
    ``target`` is required because ``SPEC.md`` orders verification *before* the
    target is prepended to ``sys.path``: a one-argument hook could only read the
    global environment, which the same document forbids.  Must raise
    ``importlib.metadata.PackageNotFoundError`` when the distribution is absent
    from ``target``.

``installed_module_origin(module_name: str, *, target: Path) -> Path``
    Module-origin hook, also target-scoped, returning the directory the module
    resolved from.  The module name need not equal the distribution name.

The harness asserts the ``target`` it is handed is the fresh target it simulated,
so a globally scoped implementation fails loudly instead of passing.

**Standard library only.**  ``scripts/autograder.py`` may import nothing
third-party: it runs before the verified target exists, so a module-scope
``import packaging`` (or any other non-stdlib import) would read the student or
global environment.  ``pytest`` is the one allowed third-party import and only
inside a function body; the bundle's own ``classroom50_manifest``,
``exercise_runtime_support``, and ``exercise_metadata`` are bundle or
checkout-owned rather than installed third-party packages.

## Why native success runs in-process

The repository virtual environment has no ``pip`` (``.venv/bin/python -m pip``
exits 1), and the fixed argv that ``ACTION_PLAN.md`` Stage 3 pins offers no
offline switch: ``--isolated`` plus the mandatory ``PIP_*`` scrub rules out
``PIP_NO_INDEX``/``PIP_FIND_LINKS``, and a monkeypatch cannot cross a process
boundary.  A native child therefore cannot complete a real install in
repository tests, so the native *success* path is exercised in-process through
``main([])`` with the pip subprocess faked: real pytest still runs, only the
operating-system process boundary is given up.  Native *failure* cases that fail
before the bootstrap - missing identity variables, an unsupported assignment
type, an in-place script run - stay real child subprocesses.

## Stage 5 carry-forward

``test_builder_emits_a_schema_valid_grading_manifest_for_the_selected_records`` in
``tests/test_classroom50_bundle_stage4.py`` deliberately pins the non-canonical
``test_fixture.py`` filename of its synthetic fixture, because Stage 3 only owns
the minimum closed manifest.  Stage 5 must rename that fixture's hidden test to
``test_<exercise_key>.py`` and update ``EXPECTED_TEST_NAMES`` and
``test_builder_copies_only_required_supports_and_excludes_unrelated_files``.  That
note has to move into a Stage 5 notes section when Stage 5 is planned; it lives
here only because the plan is not this agent's to edit.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import partial
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from types import ModuleType
from typing import Any, Final, TypeGuard, cast

import pytest

from tests._classroom50_lock import lock_derived_requirements, locked_active_pins
from tests._classroom50_test_helpers import (
    ACTIVE_VARIANT_ENV_VAR,
    AUTOGRADER_FILENAME,
    REPO_ROOT,
    StagedBundle,
    native_environment,
)

AUTOGRADER_MODULE_NAME: Final[str] = "scripts.autograder"
BUNDLE_PYTEST_INI_SOURCE: Final[Path] = REPO_ROOT / "scripts" / "classroom50_pytest.ini"
BUNDLE_MANIFEST_SOURCE: Final[Path] = REPO_ROOT / "scripts" / "classroom50_manifest.py"
BUNDLE_REQUIREMENTS_NAME: Final[str] = "requirements.txt"
BUNDLE_PYTEST_INI_NAME: Final[str] = "pytest.ini"
BUNDLE_MANIFEST_NAME: Final[str] = "classroom50_manifest.py"
BUNDLE_MANIFEST_JSON_NAME: Final[str] = "grading_manifest.json"
SEAM_BOOTSTRAP: Final[str] = "bootstrap_native_dependencies"
SEAM_IMPORT_PYTEST: Final[str] = "import_verified_pytest"
SEAM_INSTALLED_VERSION: Final[str] = "installed_distribution_version"
SEAM_INSTALLED_ORIGIN: Final[str] = "installed_module_origin"
SEAM_NAMES: Final[tuple[str, ...]] = (
    SEAM_BOOTSTRAP,
    SEAM_IMPORT_PYTEST,
    SEAM_INSTALLED_VERSION,
    SEAM_INSTALLED_ORIGIN,
)

# The documented pip invocation flags and timeout, in order.
NATIVE_PIP_TIMEOUT_SECONDS: Final[int] = 120
PIP_FLAG_ARGUMENTS: Final[tuple[str, ...]] = (
    "--isolated",
    "install",
    "--disable-pip-version-check",
    "--no-input",
    "--no-cache-dir",
    "--upgrade",
)
PIP_ENV_PREFIX: Final[str] = "PIP_"
PYTEST_DISTRIBUTION: Final[str] = "pytest"

MISMATCHED_VERSION: Final[str] = "0.0.0-stage3-fixture"
FAKE_INSTALL_MARKER: Final[str] = "stage3-fake-install.txt"


def load_autograder_module() -> ModuleType:
    """Import ``scripts/autograder.py`` as a module so its seams can be exercised."""
    return importlib.import_module(AUTOGRADER_MODULE_NAME)


def load_bundle_autograder(monkeypatch: pytest.MonkeyPatch, bundle: Path) -> ModuleType:
    """Execute the staged bundle's own ``autograder.py`` as a module.

    Local dry-run mode resolves its bundle root from the script's parent, so an
    in-process local run has to execute the bundle-local copy - exactly what the
    child process runs - rather than the repository source, whose parent is
    ``scripts/`` and has no ``exercise_runtime_support`` beside it.  The module is
    registered under a unique name for the duration of the test and removed again by
    ``monkeypatch``.

    Args:
        monkeypatch: Fixture that owns the temporary ``sys.modules`` registration.
        bundle: The staged bundle root holding ``autograder.py``.

    Returns:
        The freshly executed bundle-local grader module.
    """
    script = bundle / AUTOGRADER_FILENAME
    name = f"stage3_bundle_autograder_{id(bundle):x}"
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None and spec.loader is not None, f"Cannot load {script}."
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def seam(module: ModuleType, name: str) -> Callable[..., Any]:
    """Return the locked autograder seam ``name``, or fail with the contract text."""
    candidate = getattr(module, name, None)
    assert callable(candidate), (
        f"scripts/autograder.py does not provide the {name!r} seam yet; the "
        "contract is documented in tests/_classroom50_bootstrap.py."
    )
    return candidate


def missing_seams(module: ModuleType) -> list[str]:
    """Return the locked seam names that ``module`` does not yet provide."""
    return [name for name in SEAM_NAMES if not callable(getattr(module, name, None))]


def bundle_files(root: Path) -> frozenset[Path]:
    """Return every file under ``root``, ignoring directories a run may leave empty."""
    return frozenset(path for path in root.rglob("*") if path.is_file())


def is_manifest_records(value: object) -> TypeGuard[list[dict[str, Any]]]:
    """Return True when ``value`` is a list of JSON grading-manifest record objects."""
    if not isinstance(value, list):
        return False
    return all(isinstance(record, dict) for record in cast("list[Any]", value))


@dataclass(frozen=True)
class PipInvocation:
    """One recorded ``subprocess.run`` call made by the native bootstrap."""

    argv: list[str]
    env: Mapping[str, str]
    timeout: float | None


@dataclass
class BootstrapHarness:
    """Fake pip, version discovery, and origin checks for one native run.

    The fakes are installed on the real ``subprocess`` module and on the
    autograder's own verification seams, so the bootstrap under test runs its
    genuine code path - target lifecycle, environment scrub, target-scoped
    verification, and ``sys.path`` order - with no network access.

    ``version_lookups`` and ``origin_lookups`` record the ``(name, target)`` pair
    the implementation asked about, so a test can assert which packages were
    verified *and* under which target.  The origin names need not equal the
    distribution names: a distribution may resolve through a differently named
    module, so count and containment, not name identity, are the safe claims.
    """

    pip_returncode: int = 0
    pip_stdout: str = ""
    pip_stderr: str = ""
    pip_exception: BaseException | None = None
    installed_versions: dict[str, str] = field(default_factory=dict[str, str])
    absent_distributions: set[str] = field(default_factory=set[str])
    foreign_origin_distributions: set[str] = field(default_factory=set[str])
    invocations: list[PipInvocation] = field(default_factory=list[PipInvocation])
    version_lookups: list[tuple[str, Path]] = field(default_factory=list[tuple[str, Path]])
    origin_lookups: list[tuple[str, Path]] = field(default_factory=list[tuple[str, Path]])
    target: Path | None = None

    def with_installed_pins(self, pins: Mapping[str, str]) -> BootstrapHarness:
        """Seed the versions the fake install reports for every pin."""
        self.installed_versions.update(pins)
        return self

    def patch(self, monkeypatch: pytest.MonkeyPatch, module: ModuleType) -> None:
        """Install the fake subprocess, version, and origin seams.

        Every missing seam is reported at once, so a test names the whole contract
        rather than the first missing callable.  ``subprocess.Popen``,
        ``check_call``, and ``check_output`` are replaced with recorders that fail,
        so an implementation that installs through them cannot reach the network.
        """
        assert missing_seams(module) == [], (
            f"scripts/autograder.py must provide {SEAM_NAMES}; the contract is "
            "documented in tests/_classroom50_bootstrap.py."
        )
        monkeypatch.setattr(subprocess, "run", self._run)
        monkeypatch.setattr(subprocess, "Popen", self._refuse_other_launcher)
        monkeypatch.setattr(subprocess, "check_call", self._refuse_other_launcher)
        monkeypatch.setattr(subprocess, "check_output", self._refuse_other_launcher)
        monkeypatch.setattr(module, SEAM_INSTALLED_VERSION, self._installed_version)
        monkeypatch.setattr(module, SEAM_INSTALLED_ORIGIN, self._installed_origin)

    def _refuse_other_launcher(self, *args: Any, **kwargs: Any) -> Any:
        """Fail loudly so no other subprocess entry point can reach the network."""
        raise AssertionError(
            "the native install must use subprocess.run(argv, env=..., timeout=...); "
            f"another entry point was called with {args!r} {kwargs!r}"
        )

    def _recorded_argv(self, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> list[str]:
        """Return the argument vector of a recorded ``subprocess.run`` call."""
        if "argv" in kwargs:
            return [str(value) for value in kwargs["argv"]]
        return [str(value) for value in (args[0] if len(args) == 1 else args)]

    def _run(self, *args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Stand in for ``subprocess.run`` and record the pip invocation."""
        argv = self._recorded_argv(args, kwargs)
        raw_timeout = kwargs.get("timeout")
        timeout_value = float(raw_timeout) if raw_timeout is not None else None
        self.invocations.append(
            PipInvocation(
                argv=argv,
                env=dict(kwargs["env"]) if "env" in kwargs else dict(os.environ),
                timeout=timeout_value,
            )
        )
        assert "--target" in argv, f"the native install must pass --target; recorded argv {argv}."
        self.target = Path(argv[argv.index("--target") + 1])
        if self.pip_exception is not None:
            raise self.pip_exception
        self._materialise_target()
        return subprocess.CompletedProcess(
            argv, self.pip_returncode, self.pip_stdout, self.pip_stderr
        )

    def _assert_fresh_target(self, target: Path) -> Path:
        """Return the fresh target, or fail if the caller asked about another one.

        ``SPEC.md`` verifies versions and origins *before* the target is prepended
        to ``sys.path``, so the hooks have to be told which directory to read; a
        globally scoped lookup would silently read the student or global
        environment instead.
        """
        assert self.target is not None, "no fresh target was installed yet."
        assert Path(target) == self.target, (
            f"verification must be scoped to the fresh target {self.target}, not {target}."
        )
        return self.target

    def _materialise_target(self) -> None:
        """Create the fresh target and the fake install marker inside it."""
        assert self.target is not None
        self.target.mkdir(parents=True, exist_ok=True)
        (self.target / FAKE_INSTALL_MARKER).write_text("fake install\n", encoding="utf-8")

    def _installed_version(self, distribution: str, *, target: Path) -> str:
        """Return the faked version read under ``target``, or fail like a missing one."""
        fresh = self._assert_fresh_target(target)
        self.version_lookups.append((distribution, fresh))
        if distribution in self.absent_distributions:
            raise PackageNotFoundError(distribution)
        if distribution not in self.installed_versions:
            raise PackageNotFoundError(distribution)
        return self.installed_versions[distribution]

    def _installed_origin(self, module_name: str, *, target: Path) -> Path:
        """Return a stub origin under the fresh target, or one outside it."""
        fresh = self._assert_fresh_target(target)
        self.origin_lookups.append((module_name, fresh))
        if module_name in self.foreign_origin_distributions:
            return Path(sys.prefix) / "site-packages" / module_name
        origin = fresh / module_name
        origin.mkdir(parents=True, exist_ok=True)
        if module_name != PYTEST_DISTRIBUTION:
            (origin / "__init__.py").write_text("STAGE3_FIXTURE = True\n", encoding="utf-8")
        return origin

    @property
    def invocation(self) -> PipInvocation:
        """Return the single recorded pip invocation."""
        assert len(self.invocations) == 1, (
            f"expected exactly one pip invocation, recorded {len(self.invocations)}"
        )
        return self.invocations[0]

    @property
    def version_requests(self) -> list[str]:
        """Return the distribution names whose version was read, in call order."""
        return [name for name, _ in self.version_lookups]

    @property
    def origin_requests(self) -> list[str]:
        """Return the module names whose origin was read, in call order."""
        return [name for name, _ in self.origin_lookups]

    @property
    def origin_modules(self) -> set[str]:
        """Return the distinct module names whose origin was read."""
        return {name for name, _ in self.origin_lookups}

    @property
    def pip_environment(self) -> Mapping[str, str]:
        """Return the environment the recorded pip subprocess actually saw."""
        return self.invocation.env

    @property
    def requirements_argument(self) -> str:
        """Return the ``-r`` requirements path passed to pip."""
        return self.invocation.argv[self.invocation.argv.index("-r") + 1]


def purge_bundle_imports(*roots: Path) -> None:
    """Drop modules an in-process run imported out of the staged ``roots``.

    Two leaks have to be closed after an in-process run:

    * pytest's default import mode registers a collected test module under its bare
      basename, so leaving it in ``sys.modules`` makes the *next* staged bundle look
      like an "import file mismatch" for the same module name;
    * the run imports the bundle's ``exercise_runtime_support`` copy and the student
      checkout's ``exercise_metadata`` copy, and the submodules that appear for the
      first time would otherwise stay in ``sys.modules`` pointing into a temporary
      directory that is deleted at teardown, breaking the rest of the session.

    Only modules whose file lives under ``roots`` are removed, so the running
    session keeps its own.
    """
    prefixes = tuple(f"{root}/" for root in roots)
    for name, module in list(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        if isinstance(origin, str) and origin.startswith(prefixes):
            sys.modules.pop(name, None)


def isolate_bundle_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the already-imported bundle-owned packages for one in-process run.

    ``exercise_runtime_support`` and ``exercise_metadata`` are imported by the outer
    test session, so an in-process grading run would otherwise reuse the repository
    copies and fail the package-origin check for the wrong reason.  The entries are
    *deleted* rather than hidden behind a replacement ``sys.modules`` mapping:
    CPython's own import machinery resolves names against the interpreter's real
    module table, which is the object ``sys.modules`` names, so a replacement mapping
    is only half-visible and the two import paths disagree.  ``monkeypatch`` puts
    every removed entry back on teardown, so the running session keeps its modules.
    """
    shadowed_roots = ("exercise_metadata", "exercise_runtime_support")
    for name in [
        imported for imported in sys.modules if imported.split(".", maxsplit=1)[0] in shadowed_roots
    ]:
        monkeypatch.delitem(sys.modules, name)


def child_exit_code(run: Callable[[], int]) -> int:
    """Return the child exit code for ``run``, mapping an unhandled failure to non-zero.

    ``scripts/autograder.py`` may report an infrastructure failure either as a
    non-zero return value or as an unhandled ``RuntimeError``/``SystemExit``; both
    end the child process with a non-zero status, and that status - not the
    internal reporting style - is the contract under test.
    """
    try:
        return run()
    except SystemExit as exit_request:
        return exit_request.code if isinstance(exit_request.code, int) else 1
    except RuntimeError:
        return 2


@dataclass(frozen=True)
class LocalRun:
    """One in-process local dry run plus everything that must not have happened."""

    exit_code: int
    bootstrap_calls: int
    subprocess_calls: list[tuple[tuple[Any, ...], dict[str, Any]]]
    seam_calls: list[tuple[str, tuple[Any, ...]]]


@dataclass(frozen=True)
class NativeRun:
    """One in-process native invocation and everything observed while it ran."""

    exit_code: int
    harness: BootstrapHarness
    module: ModuleType


def run_native_in_process(
    monkeypatch: pytest.MonkeyPatch,
    staged: StagedBundle,
    env_overrides: Mapping[str, object] | None = None,
    **harness_options: Any,
) -> NativeRun:
    """Run the native entry point in-process against ``staged`` with a faked install.

    The staged bundle receives the lock-derived requirements source, because a
    native run has to parse real pins; the variant, the native environment, the
    working directory, ``sys.path``, and the module table are all restored by
    ``monkeypatch`` on teardown.

    Args:
        monkeypatch: Fixture that owns every temporary mutation.
        staged: The staged bundle and student checkout to grade.
        env_overrides: Native environment overrides; an ``ABSENT`` value removes
            the key, which is how the documented optional-variable cases are set.
        harness_options: Field overrides for the :class:`BootstrapHarness`.

    Returns:
        The child's exit status plus the recording harness and the module under test.
    """
    module = load_autograder_module()
    (staged.bundle / BUNDLE_REQUIREMENTS_NAME).write_text(
        lock_derived_requirements(), encoding="utf-8"
    )
    harness = BootstrapHarness(**harness_options).with_installed_pins(locked_active_pins())
    harness.patch(monkeypatch, module)
    isolate_bundle_imports(monkeypatch)
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setenv(ACTIVE_VARIANT_ENV_VAR, "student")
    for key, value in native_environment(staged, **(env_overrides or {})).items():
        monkeypatch.setenv(key, value)
    monkeypatch.chdir(staged.student)
    try:
        exit_code = child_exit_code(lambda: module.main([]))
    finally:
        # Even an unabsorbed failure (a failing recorder, a grader ValueError, a
        # pytest collection error) must not leave modules registered against a
        # tmp_path pytest is about to delete.
        purge_bundle_imports(staged.bundle, staged.student)
    return NativeRun(exit_code=exit_code, harness=harness, module=module)


def run_local_in_process(
    monkeypatch: pytest.MonkeyPatch,
    staged: StagedBundle,
    result_path: Path,
    *,
    variant: str | None = None,
) -> LocalRun:
    """Run the local dry-run entry point in-process with every installer disabled.

    ``subprocess.run``, ``Popen``, ``check_call``, and ``check_output`` are replaced
    with recorders that fail, and each installed seam is replaced with a recorder,
    so a local run that tried to bootstrap would fail loudly instead of reaching the
    network.  The result is what a local run may do: grade the checkout, write the
    canonical result, and exit 0.

    Args:
        monkeypatch: Fixture that owns every temporary mutation.
        staged: The staged bundle and student checkout to grade.
        result_path: Local-mode result destination.
        variant: Optional dry-run variant; ``None`` grades the forced student variant.

    Returns:
        The child's exit status plus the recorded bootstrap, subprocess, and seam calls.
    """
    module = load_bundle_autograder(monkeypatch, staged.bundle)
    subprocess_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    seam_calls: list[tuple[str, tuple[Any, ...]]] = []
    bootstrap_calls: list[tuple[Any, ...]] = []

    def _record_subprocess(*args: Any, **kwargs: Any) -> Any:
        subprocess_calls.append((args, kwargs))
        raise AssertionError(f"a local dry run must not launch a subprocess: {args!r}")

    def _record_bootstrap(*args: Any, **kwargs: Any) -> Any:
        bootstrap_calls.append(args)
        raise AssertionError("a local dry run must not bootstrap native dependencies")

    for entry_point in ("run", "Popen", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, entry_point, _record_subprocess)
    if callable(getattr(module, SEAM_BOOTSTRAP, None)):
        monkeypatch.setattr(module, SEAM_BOOTSTRAP, _record_bootstrap)
    for name in SEAM_NAMES:
        if callable(getattr(module, name, None)):
            monkeypatch.setattr(module, name, partial(_record_seam, seam_calls, name))
    isolate_bundle_imports(monkeypatch)
    monkeypatch.setattr(sys, "path", list(sys.path))
    # Seed the variant so the grader's own environment write is undone on teardown
    # and cannot leave the rest of the session grading the student notebooks.
    monkeypatch.setenv(ACTIVE_VARIANT_ENV_VAR, variant or "student")
    monkeypatch.chdir(staged.bundle)
    arguments = ["--student-root", str(staged.student), "--result", str(result_path)]
    if variant is not None:
        arguments.extend(["--variant", variant])
    try:
        exit_code = child_exit_code(lambda: module.main(arguments))
    finally:
        purge_bundle_imports(staged.bundle, staged.student)
    return LocalRun(
        exit_code=exit_code,
        bootstrap_calls=len(bootstrap_calls),
        subprocess_calls=subprocess_calls,
        seam_calls=seam_calls,
    )


def _record_seam(calls: list[tuple[str, tuple[Any, ...]]], name: str) -> Callable[..., Any]:
    """Return a recorder that notes a seam call and then fails the local run."""

    def recorder(*args: Any, **kwargs: Any) -> Any:
        calls.append((name, args))
        raise AssertionError(f"a local dry run must not call {name}()")

    return recorder
