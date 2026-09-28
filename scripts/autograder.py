"""Generic Classroom 50 grader for native and local per-assignment bundles.

The bundle directory holding this script is the discovery root: hidden tests
are collected from ``<bundle>/exercises/<construct>/<exercise_key>/tests/``
only, never from the student checkout. The bundle root is prepended to
``sys.path`` so exercise-local support modules resolve into the bundle, while
``exercise_metadata`` resolves from the student checkout so notebooks resolve
to student work.

Exactly one of two invocation modes is selected per run:

* Native mode is a no-argument invocation. The Classroom 50 runner starts this
  child from the student checkout, so the current working directory is the
  student root, ``CLASSROOM50_BUNDLE_DIR`` is the bundle root, and the result is
  ``result.json`` in the current working directory.
* Local mode is a dry run selected by supplying ``--student-root`` and
  ``--result`` together; either argument alone is a usage error. Its bundle root
  is this script's parent, so local runs are supported only from a built-bundle
  copy, never in place.

The graded run always forces ``PYTUTOR_ACTIVE_VARIANT=student``. ``--variant
solution`` exists for the local dry run only.

Native mode is independent of the student's Python environment. The bundle's own
``requirements.txt`` is installed into a fresh bundle-local target with the fixed
isolated pip invocation, every actively required version and module origin is
verified under that target, and only the verified target is prepended to
``sys.path``; pytest is imported after that, never at module load. A local dry
run is a developer-environment check, so it never installs anything.

Exit semantics follow the documented contract: pytest outcomes 0 (all passed)
and 1 (tests ran and some failed) are completed runs, so the grader writes the
``classroom50/result/v1`` payload and exits 0 with pass/fail carried in the
payload. Any other pytest exit (interrupted collection, internal or usage
error, no tests collected) — or an empty discovery set — is an infrastructure
error: the grader exits non-zero and writes no completed payload. A missing or
invalid native environment, a graded package that does not resolve from its
contracted root, or a dependency bootstrap that cannot be trusted is reported the
same way. Any other exception escaping a grading run is a bug and is left to
surface as a traceback. Any pre-existing result output is removed before the
grading attempt, so a stale result file can never survive an infrastructure
failure and be misread as a grade.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from argparse import Namespace
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.machinery import PathFinder
from importlib.metadata import PackageNotFoundError, distributions
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import pytest

RESULT_SCHEMA: Final[str] = "classroom50/result/v1"
ACTIVE_VARIANT_ENV_VAR: Final[str] = "PYTUTOR_ACTIVE_VARIANT"
BUNDLE_DIR_ENV_VAR: Final[str] = "CLASSROOM50_BUNDLE_DIR"
NATIVE_RESULT_FILENAME: Final[str] = "result.json"
ASSIGNMENT_TYPE_ENV_VAR: Final[str] = "ASSIGNMENT_TYPE"
SUPPORTED_ASSIGNMENT_TYPES: Final[tuple[str, ...]] = ("individual", "group", "team")
OWNER_ENV_VARS: Final[tuple[str, ...]] = ("OWNER", "USERNAME")
DATETIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"

# The four files the builder emits into the bundle root before the grader can use
# the bundle. Stage 3 only requires them to be present; a later stage loads the
# shared validator to select the hidden tests the manifest lists.
REQUIREMENTS_FILENAME: Final[str] = "requirements.txt"
TARGET_CONTRACT_FILENAMES: Final[tuple[str, ...]] = (
    REQUIREMENTS_FILENAME,
    "pytest.ini",
    "classroom50_manifest.py",
    "grading_manifest.json",
)

# The native install target is always a fresh directory beneath the bundle's
# runtime directory, never the bundle root, the student checkout, or the grading
# interpreter's own site-packages.
NATIVE_RUNTIME_DIRNAME: Final[str] = "runtime"
NATIVE_TARGET_DIRNAME: Final[str] = "site-packages"

# The fixed native install invocation and its bound. ``--isolated`` plus the
# inherited ``PIP_*`` scrub keep a hostile pip configuration, index, find-links,
# user setting, or ``PIP_TARGET`` from redirecting or replacing the target.
NATIVE_PIP_FLAGS: Final[tuple[str, ...]] = (
    "--isolated",
    "install",
    "--disable-pip-version-check",
    "--no-input",
    "--no-cache-dir",
    "--upgrade",
)
NATIVE_PIP_TIMEOUT_SECONDS: Final[int] = 120
PIP_ENV_PREFIX: Final[str] = "PIP_"

# The closed requirement-line grammar the committed native requirements source
# uses: one exact ``name==version`` pin, optionally restricted to a platform with
# the single documented ``sys_platform == "..."`` marker, in either quote style and
# with whitespace tolerated around the ``;`` and ``==``. ``packaging`` cannot parse
# it here because the verified target does not exist yet.
_REQUIREMENT_LINE: Final[re.Pattern[str]] = re.compile(
    r"(?P<distribution>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[A-Za-z0-9][A-Za-z0-9.+!-]*)"
    r"""(?:\s*;\s*sys_platform\s*==\s*["'](?P<platform>[A-Za-z0-9_]+)["'])?"""
)
_NORMALISED_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"[-_.]+")

# Local dry runs are schema-valid but explicitly non-uploadable: these exact
# values must never be mistaken for Classroom 50 identity or collected scores.
LOCAL_IDENTITY: Final[Mapping[str, str]] = MappingProxyType(
    {
        "classroom": "local",
        "assignment": "local",
        "assignment_type": "individual",
        "owner": "local",
        "submission": "submit/local",
        "commit": "local://commit",
        "release": "local://release",
        "review": "local://review",
    }
)


class GradingInfrastructureError(RuntimeError):
    """Base class for the documented failures that write no result and exit non-zero.

    Only these types are reported as infrastructure errors. Anything else escaping a
    grading run is a bug, so it is left to surface as a traceback rather than being
    reported as a deliberate failure with no diagnostic detail.
    """


class GradingConfigurationError(GradingInfrastructureError):
    """Raised when an invocation or the native environment cannot be graded."""


class PackageOriginError(GradingInfrastructureError):
    """Raised when a graded package does not resolve from its contracted root."""


class DependencyBootstrapError(GradingInfrastructureError):
    """Raised when the native dependency target cannot be installed or trusted."""


@dataclass(frozen=True)
class GradingRequest:
    """One resolved grading request: the roots, the variant, and the result identity."""

    bundle_root: Path
    student_root: Path
    variant: str
    identity: Mapping[str, str]
    native: bool


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    """Parse the grader command line, rejecting a half-supplied local pair."""
    parser = argparse.ArgumentParser(
        description="Grade a student checkout with bundled hidden tests.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--student-root",
        type=Path,
        help="Checkout to grade; selects local mode together with --result.",
    )
    parser.add_argument(
        "--result",
        type=Path,
        help="Local mode destination for the classroom50/result/v1 JSON payload.",
    )
    parser.add_argument(
        "--variant",
        choices=("student", "solution"),
        default="student",
        help="Notebook variant to expose; solution is local dry-run only.",
    )
    args = parser.parse_args(argv)
    if (args.student_root is None) != (args.result is None):
        parser.error("--student-root and --result must be supplied together.")
    if args.student_root is None and args.variant != "student":
        parser.error("--variant is local dry-run only; supply --student-root and --result.")
    return args


def _resolve_result_path(args: Namespace) -> Path:
    """Return the result destination implied by the requested mode.

    The destination is known before the native environment is validated, so a
    stale result is removed even when validation then fails.
    """
    if args.result is None:
        return Path.cwd() / NATIVE_RESULT_FILENAME
    return Path(args.result)


def _resolve_grading_request(args: Namespace) -> GradingRequest:
    """Return the request implied by a native invocation or by the local pair."""
    if args.student_root is None:
        return _native_grading_request()
    return GradingRequest(
        bundle_root=Path(__file__).resolve().parent,
        student_root=Path(args.student_root),
        variant=args.variant,
        identity=LOCAL_IDENTITY,
        native=False,
    )


def _native_grading_request() -> GradingRequest:
    """Return the request the Classroom 50 runner implies with no arguments."""
    return GradingRequest(
        bundle_root=Path(_required_native_value(BUNDLE_DIR_ENV_VAR)).resolve(),
        student_root=Path.cwd(),
        variant="student",
        identity=_native_identity(),
        native=True,
    )


def _required_native_value(name: str) -> str:
    """Return a required native environment value or fail naming the variable."""
    value = os.environ.get(name, "")
    if not value:
        raise GradingConfigurationError(f"Required native environment variable {name} is not set.")
    return value


def _native_identity() -> dict[str, str]:
    """Return the documented native result identity fields."""
    commit = _required_native_value("COMMIT_URL")
    return {
        "classroom": _required_native_value("CLASSROOM"),
        "assignment": _required_native_value("ASSIGNMENT"),
        "assignment_type": _native_assignment_type(),
        "owner": _native_owner(),
        "submission": _required_native_value("SUBMISSION_TAG"),
        "commit": commit,
        "release": _required_native_value("RELEASE_URL"),
        "review": os.environ.get("REVIEW_URL") or commit,
    }


def _native_assignment_type() -> str:
    """Return the native ``ASSIGNMENT_TYPE`` once it is known to be supported."""
    assignment_type = _required_native_value(ASSIGNMENT_TYPE_ENV_VAR)
    if assignment_type not in SUPPORTED_ASSIGNMENT_TYPES:
        supported = ", ".join(SUPPORTED_ASSIGNMENT_TYPES)
        raise GradingConfigurationError(
            f"Unsupported ASSIGNMENT_TYPE {assignment_type!r}; expected one of {supported}."
        )
    return assignment_type


def _native_owner() -> str:
    """Return the submission owner from ``OWNER``, falling back to ``USERNAME``."""
    for name in OWNER_ENV_VARS:
        value = os.environ.get(name, "")
        if value:
            return value
    raise GradingConfigurationError(
        f"No submission owner: set {' or '.join(OWNER_ENV_VARS)} for the result identity."
    )


class _OutcomeCollector:
    """Collect one terminal outcome per pytest leaf case."""

    def __init__(self) -> None:
        """Initialise the ordered outcome store."""
        self.nodeids: list[str] = []
        self.statuses: dict[str, str] = {}
        self.exercise_keys: dict[str, str] = {}

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        """Record the owning exercise key for each collected leaf case."""
        for item in items:
            if item.nodeid not in self.exercise_keys:
                self.nodeids.append(item.nodeid)
            self.exercise_keys[item.nodeid] = _exercise_key_for_path(item.path)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        """Record the terminal outcome for a single report phase.

        Every phase counts, and a failure is terminal: a case whose call phase
        passed but whose teardown failed is recorded as failed rather than
        keeping the earlier pass.
        """
        nodeid = report.nodeid
        if nodeid not in self.nodeids:
            self.nodeids.append(nodeid)
        if nodeid not in self.statuses:
            self.statuses[nodeid] = "pending"
        if report.failed:
            self.statuses[nodeid] = "failed"
        elif report.skipped:
            if self.statuses[nodeid] == "pending":
                self.statuses[nodeid] = "skipped"
        elif report.when == "call" and report.passed:
            self.statuses[nodeid] = "passed"


def _leaf_name(nodeid: str) -> str:
    """Return the leaf ``test_*.py::test_name`` portion of a pytest node id."""
    head, separator, tail = nodeid.partition("::")
    filename = Path(head).name
    return filename + (separator + tail if separator else "")


def _exercise_key_for_path(path: Path) -> str:
    """Return the exercise key owning a bundled hidden test file path."""
    for parent in path.parents:
        if parent.name == "tests":
            return parent.parent.name
    raise ValueError(f"Cannot derive an exercise key from test path {path!r}.")


def _exercise_key_for_nodeid(nodeid: str, exercise_keys: dict[str, str]) -> str:
    """Return the exercise key recorded at collection time for a node id."""
    try:
        return exercise_keys[nodeid]
    except KeyError:
        head = nodeid.split("::", 1)[0]
        return _exercise_key_for_path(Path(head))


def configure_bundle_paths(bundle_root: Path, student_root: Path) -> None:
    """Order ``sys.path`` as the verified target, the bundle root, then the checkout.

    The bundle ships its own ``exercise_runtime_support`` copy, so it must come
    first; ``exercise_metadata`` ships only in the student checkout, so the checkout
    follows right behind it.  A verified native target already under the bundle's
    runtime directory keeps the place in front of them that the bootstrap gave it, so
    re-ordering the pair cannot displace it.
    """
    ordered = (str(bundle_root), str(student_root))
    runtime_root = (bundle_root / NATIVE_RUNTIME_DIRNAME).resolve()
    in_front = [
        entry
        for entry in sys.path
        if entry not in ordered and Path(entry).is_relative_to(runtime_root)
    ]
    for entry in (*in_front, *ordered):
        while entry in sys.path:
            sys.path.remove(entry)
    sys.path[:0] = [*in_front, *ordered]


def discover_hidden_tests(bundle_root: Path) -> list[Path]:
    """Return the bundled hidden test files in a deterministic order."""
    tests_root = bundle_root / "exercises"
    if not tests_root.is_dir():
        return []
    return sorted(path for path in tests_root.rglob("tests/test_*.py") if path.is_file())


def _check_package_origins(bundle_root: Path, student_root: Path) -> None:
    """Fail fast unless runtime and metadata packages resolve as designed."""
    import exercise_metadata
    import exercise_runtime_support

    runtime_dir = Path(exercise_runtime_support.__file__).resolve().parent
    metadata_dir = Path(exercise_metadata.__file__).resolve().parent
    if runtime_dir != bundle_root / "exercise_runtime_support":
        raise PackageOriginError(
            "exercise_runtime_support resolved to "
            f"{runtime_dir}, not the bundle copy under {bundle_root}."
        )
    if metadata_dir.parent != student_root:
        raise PackageOriginError(
            "exercise_metadata resolved to "
            f"{metadata_dir}, not the student checkout under {student_root}."
        )


# ---------------------------------------------------------------------------
# The native dependency bootstrap.
#
# Everything in this section runs before the verified target is on ``sys.path``, so
# it uses the standard library only: no ``packaging``, no ``uv``, and no read of the
# student's own dependency manifest. The bundle's committed requirements file is the
# sole install source.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RequiredPackage:
    """One exact pin the bundle requires on the platform this run executes on."""

    distribution: str
    version: str


def _require_target_contract(bundle_root: Path) -> None:
    """Fail fast unless the bundle carries every file the native run depends on.

    The shared validator among them is only required to be present at this stage; a
    later stage loads it here to select the hidden tests the manifest lists.
    """
    missing = [name for name in TARGET_CONTRACT_FILENAMES if not (bundle_root / name).is_file()]
    if missing:
        raise DependencyBootstrapError(
            f"The bundle at {bundle_root} is missing {missing}; rebuild it before grading."
        )


def _required_packages(requirements: Path) -> list[RequiredPackage]:
    """Return the pins ``requirements`` requires on this platform.

    The committed source is a closed set of exact pins with at most the documented
    ``sys_platform == "..."`` marker, so it is parsed with a matching small grammar
    rather than with ``packaging.requirements``: the bootstrap runs before the
    verified target exists, and importing ``packaging`` then would read the student
    or global environment - the very leak this stage closes.

    The accepted grammar is exactly ``name==version`` with an optional
    ``; sys_platform == "platform"`` marker, quoted either way, with whitespace
    tolerated around the ``;`` and ``==``.  A range, an extras request, a hash, an
    inline comment, a URL, a wildcard, or any other marker operator is a contract
    violation and is rejected rather than tolerated.  A whole-line comment is
    ignored, as is a pin whose marker selects another platform.

    Args:
        requirements: The bundle's own ``requirements.txt``.

    Returns:
        The pins whose marker holds for this platform, in file order.

    Raises:
        DependencyBootstrapError: If a line is not one exact pin in that grammar.
    """
    pins: list[RequiredPackage] = []
    for line in requirements.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        match = _REQUIREMENT_LINE.fullmatch(text)
        if match is None:
            raise DependencyBootstrapError(
                f"Unsupported requirement line {text!r} in {requirements}; the native "
                "requirements source is a list of exact 'name==version' pins."
            )
        platform = match["platform"]
        if platform is not None and platform != sys.platform:
            continue
        pins.append(RequiredPackage(match["distribution"], match["version"]))
    return pins


def _remove_tree(path: Path) -> None:
    """Remove ``path`` and everything under it when it exists."""
    if path.exists():
        shutil.rmtree(path)


def _fresh_target(bundle_root: Path) -> Path:
    """Remove any previous target and create an empty one beneath the bundle.

    The target is bundle-local and newly created every run, so it is never
    populated from a student-controlled or global directory and a previous run's
    packages can never survive into this one.
    """
    target = bundle_root / NATIVE_RUNTIME_DIRNAME / NATIVE_TARGET_DIRNAME
    _remove_tree(target)
    target.mkdir(parents=True)
    return target


def _scrubbed_pip_environment() -> dict[str, str]:
    """Return the inherited environment with every ``PIP_*`` key removed."""
    return {
        name: value for name, value in os.environ.items() if not name.startswith(PIP_ENV_PREFIX)
    }


def _run_pip_install(target: Path, requirements: Path) -> None:
    """Run the fixed isolated pip invocation into the fresh target.

    Args:
        target: The fresh bundle-local install target.
        requirements: The bundle's own requirements file.

    Raises:
        DependencyBootstrapError: If pip is missing, fails, or overruns the bound.
    """
    argv = [
        sys.executable,
        "-m",
        "pip",
        *NATIVE_PIP_FLAGS,
        "--target",
        str(target),
        "-r",
        str(requirements),
    ]
    try:
        completed = subprocess.run(
            argv,
            env=_scrubbed_pip_environment(),
            timeout=NATIVE_PIP_TIMEOUT_SECONDS,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DependencyBootstrapError(
            f"pip could not install {requirements} into {target}: {error}"
        ) from error
    if completed.returncode != 0:
        raise DependencyBootstrapError(
            f"pip exited {completed.returncode} installing {requirements} into {target}."
            f"\n{completed.stderr}"
        )


def _normalised_name(name: str | None) -> str:
    """Return a PEP 503-normalised distribution name for comparison."""
    return _NORMALISED_NAME_PATTERN.sub("-", name or "").lower()


def installed_distribution_version(distribution: str, *, target: Path) -> str:
    """Return the version of ``distribution`` installed under ``target``.

    Discovery is scoped to ``target`` alone, never to the interpreter's own
    environment, because the target is verified before it is put on ``sys.path``.

    Args:
        distribution: Distribution name as pinned in the bundle requirements file.
        target: The fresh bundle-local install target to read from.

    Returns:
        The installed version string.

    Raises:
        PackageNotFoundError: If ``target`` holds no such distribution.
    """
    wanted = _normalised_name(distribution)
    for installed in distributions(path=[str(target)]):
        if _normalised_name(installed.metadata["Name"]) == wanted:
            return str(installed.version)
    raise PackageNotFoundError(distribution)


def installed_module_origin(module_name: str, *, target: Path) -> Path:
    """Return the directory ``module_name`` resolves from inside ``target``.

    The search path is ``target`` alone, never ``sys.path``, because the target is
    verified before it is put on ``sys.path``.

    Args:
        module_name: Importable module name to locate; it need not equal the
            distribution name that provides it.
        target: The fresh bundle-local install target to search.

    Returns:
        The package directory, or the containing directory of a plain module.

    Raises:
        ModuleNotFoundError: If ``target`` provides no such module.
    """
    spec = PathFinder.find_spec(module_name, [str(target)])
    if spec is None:
        raise ModuleNotFoundError(
            f"No module named {module_name!r} in the verified target {target}.",
            name=module_name,
        )
    if spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations)))
    if spec.origin is None:
        raise ModuleNotFoundError(
            f"Module {module_name!r} in the verified target {target} has no file origin.",
            name=module_name,
        )
    return Path(spec.origin).parent


def _verify_installed_versions(pins: Sequence[RequiredPackage], target: Path) -> None:
    """Fail unless every active pin is installed at its exact version."""
    for pin in pins:
        try:
            found = installed_distribution_version(pin.distribution, target=target)
        except PackageNotFoundError as error:
            raise DependencyBootstrapError(
                f"{pin.distribution} is not installed in the verified target {target}."
            ) from error
        if found != pin.version:
            raise DependencyBootstrapError(
                f"{pin.distribution} {found} is installed in {target}, not the pinned "
                f"{pin.version}."
            )


def _verify_installed_origins(pins: Sequence[RequiredPackage], target: Path) -> None:
    """Fail unless every active pin resolves from a directory inside the target."""
    root = target.resolve()
    for pin in pins:
        try:
            origin = installed_module_origin(pin.distribution, target=target)
        except ModuleNotFoundError as error:
            raise DependencyBootstrapError(
                f"{pin.distribution} provides no importable module in {target}."
            ) from error
        if not origin.resolve().is_relative_to(root):
            raise DependencyBootstrapError(
                f"{pin.distribution} resolves to {origin}, outside the verified target {root}."
            )


def _prepend_verified_target(target: Path) -> None:
    """Put the verified target ahead of the bundle root and the student checkout.

    ``configure_bundle_paths`` has already placed the bundle and the checkout at the
    front, so inserting the verified target at index 0 completes the documented
    order: verified target, then bundle root, then student checkout.
    """
    while str(target) in sys.path:
        sys.path.remove(str(target))
    sys.path.insert(0, str(target))


def bootstrap_native_dependencies(bundle_root: Path) -> Path:
    """Install and verify the native requirement closure in a fresh bundle target.

    The bundle's committed requirements file is the only install source, the
    target is removed and recreated first, and every actively required version and
    module origin is verified under it before it is put on ``sys.path``. Any
    failure removes the target again, so no partially installed content can be
    picked up by a later run, and the child writes no result and exits non-zero.

    Args:
        bundle_root: Root of the bundle the runner extracted.

    Returns:
        The verified, freshly installed bundle-local target.

    Raises:
        DependencyBootstrapError: If the target cannot be installed or trusted.
    """
    _require_target_contract(bundle_root)
    requirements = bundle_root / REQUIREMENTS_FILENAME
    pins = _required_packages(requirements)
    target = _fresh_target(bundle_root)
    try:
        _run_pip_install(target, requirements)
        _verify_installed_versions(pins, target)
        _verify_installed_origins(pins, target)
    except Exception:
        # The verification hooks read an arbitrary installed tree, so a corrupt
        # ``.dist-info`` can raise anything at all. Whatever goes wrong, the target
        # goes with it; the exception is re-raised unchanged so the declared
        # ``DependencyBootstrapError`` still reaches the caller. An interrupt is a
        # ``BaseException`` and deliberately survives this handler: the next run's
        # ``_fresh_target`` removes the leftover directory before installing.
        _remove_tree(target)
        raise
    _prepend_verified_target(target)
    return target


def import_verified_pytest(bundle_root: Path) -> ModuleType:
    """Install the verified native target and return the pytest module to grade with.

    The bootstrap runs first, so ``pytest`` is imported only once the fresh target
    is installed, version-checked, origin-checked, and prepended to ``sys.path``.
    A local dry run does not come here; it grades with the developer's own pytest.

    Args:
        bundle_root: Root of the bundle the runner extracted.

    Returns:
        The imported pytest module.
    """
    bootstrap_native_dependencies(bundle_root)
    import pytest

    return pytest


def _grading_pytest(request: GradingRequest) -> ModuleType:
    """Return the pytest module this run grades with.

    Native mode grades with the verified fresh target's pytest; a local dry run is
    a developer-environment check and installs nothing.
    """
    if request.native:
        return import_verified_pytest(request.bundle_root)
    import pytest

    return pytest


def _utc_timestamp() -> str:
    """Return the current UTC time in the documented result format."""
    return datetime.now(UTC).strftime(DATETIME_FORMAT)


def _result_row(collector: _OutcomeCollector, nodeid: str) -> dict[str, object]:
    """Return the canonical result row for one collected leaf case."""
    exercise_key = _exercise_key_for_nodeid(nodeid, collector.exercise_keys)
    passed = collector.statuses.get(nodeid) == "passed"
    return {
        "test-name": f"{exercise_key}::{_leaf_name(nodeid)}",
        "passed": passed,
        "score": 1 if passed else 0,
        "max-score": 1,
    }


def build_result_payload(
    collector: _OutcomeCollector, identity: Mapping[str, str]
) -> dict[str, object]:
    """Build the classroom50/result/v1 payload from collected outcomes."""
    rows = [_result_row(collector, nodeid) for nodeid in collector.nodeids]
    return {
        "schema": RESULT_SCHEMA,
        **identity,
        "datetime": _utc_timestamp(),
        "score": sum(1 for row in rows if row["passed"]),
        "max-score": len(rows),
        "tests": rows,
    }


def invalidate_result(result_path: Path) -> None:
    """Remove any pre-existing result output before a grading attempt."""
    result_path.unlink(missing_ok=True)


def _run_pytest(
    pytest_module: ModuleType, test_files: list[str], collector: _OutcomeCollector
) -> int:
    """Return pytest's exit code for the bundled hidden tests.

    This is the only pytest invocation in the module, so the native dependency
    bootstrap can own the import and the environment it runs in.
    """
    return int(
        pytest_module.main(
            [*test_files, "-q", "-p", "no:cacheprovider"],
            plugins=[collector],
        )
    )


def run_bundle(request: GradingRequest) -> tuple[dict[str, object] | None, int]:
    """Grade the checkout and return the payload plus the process exit code.

    Completed pytest runs (exits 0 and 1) return a payload with exit 0.
    Infrastructure failures (any other pytest exit, or no hidden tests at all)
    return no payload with a non-zero exit. The caller removes any
    pre-existing result output beforehand, so nothing stale remains.
    """
    os.environ[ACTIVE_VARIANT_ENV_VAR] = request.variant
    student_root = request.student_root.resolve()
    configure_bundle_paths(request.bundle_root, student_root)
    # Order matters: the bundle and student package origins are checked before the
    # bootstrap and pytest is imported after it, so an unrelated origin failure is
    # never reported as a dependency failure.
    _check_package_origins(request.bundle_root, student_root)
    pytest_module = _grading_pytest(request)
    test_files = discover_hidden_tests(request.bundle_root)
    if not test_files:
        print("No bundled hidden tests found; cannot grade.", file=sys.stderr)
        return None, 2
    collector = _OutcomeCollector()
    pytest_exit = _run_pytest(pytest_module, [str(path) for path in test_files], collector)
    if pytest_exit in (0, 1):
        return build_result_payload(collector, request.identity), 0
    print(
        f"pytest exited with {pytest_exit}; infrastructure error, no grade written.",
        file=sys.stderr,
    )
    return None, pytest_exit


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bundle grader and write the result document for completed runs."""
    args = parse_args(argv)
    result_path = _resolve_result_path(args)
    invalidate_result(result_path)
    try:
        request = _resolve_grading_request(args)
    except GradingConfigurationError as error:
        print(error, file=sys.stderr)
        return 2
    if not request.student_root.is_dir():
        print(f"Student checkout not found: {request.student_root}", file=sys.stderr)
        return 2
    try:
        payload, exit_code = run_bundle(request)
    except GradingInfrastructureError as error:
        # Identity, package-origin, and dependency failures are infrastructure
        # errors by contract: report them and write no completed result. Any other
        # exception is a bug and must surface as a traceback, which the outer runner
        # still treats as a non-zero child exit.
        print(error, file=sys.stderr)
        return 2
    if payload is None:
        return exit_code
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
