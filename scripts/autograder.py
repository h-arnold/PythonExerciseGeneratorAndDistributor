"""Generic Classroom 50 grader for teacher-side assignment bundles.

The bundle directory holding this script is the discovery root: hidden tests
are collected from ``<bundle>/exercises/<construct>/<exercise_key>/tests/``
only, never from the student checkout. The bundle root is prepended to
``sys.path`` so exercise-local support modules resolve into the bundle, while
``exercise_metadata`` resolves from the student checkout so notebooks resolve
to student work.

The grader has two invocation modes:

- **Classroom 50 mode** takes no arguments. Classroom 50 starts the child in
  the student checkout, so the current working directory is the student root,
  the bundle root is this script's own parent directory, the result is
  ``./result.json`` in the current working directory, and the graded notebook
  variant is forced to ``student``. The identity fields are read from the
  documented runner environment variables.
- **Local mode** takes ``--student-root`` and ``--result`` as a pair. It grades
  the named checkout, writes the named result path, and emits the documented
  non-uploadable ``local`` identity values. ``--variant solution`` exposes the
  solution notebooks for a dry run.

Classroom 50 mode installs the grading dependencies into the grading
interpreter, because that interpreter does not ship this runtime's test
dependencies, and does so before importing pytest. Local mode installs
nothing and uses the developer's own environment.

Exit semantics follow the documented contract: pytest outcomes 0 (all passed)
and 1 (tests ran and some failed) are completed runs, so the grader writes the
``classroom50/result/v1`` payload and exits 0 with pass/fail carried in the
payload. Any other pytest exit (interrupted collection, internal or usage
error, no tests collected) — or an empty discovery set — is an infrastructure
error: the grader exits non-zero and writes no completed payload. A missing
required environment value, an unsupported assignment type, and a failed
dependency install are grading failures of the same kind. Any pre-existing
result output is removed before the grading attempt, so a stale result file can
never survive a failure and be misread as a grade.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from argparse import Namespace
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    import pytest

RESULT_SCHEMA = "classroom50/result/v1"
RESULT_FILENAME = "result.json"
ACTIVE_VARIANT_ENV_VAR = "PYTUTOR_ACTIVE_VARIANT"
# pytest runs the bundle and the runtime reporting module imports tabulate
# directly, so both are needed by the grading interpreter.
GRADING_PACKAGES = ("pytest", "tabulate")
SUPPORTED_ASSIGNMENT_TYPES = ("individual", "group", "team")
REQUIRED_RUNNER_VARIABLES = (
    "CLASSROOM",
    "ASSIGNMENT",
    "ASSIGNMENT_TYPE",
    "SUBMISSION_TAG",
    "COMMIT_URL",
    "RELEASE_URL",
)


class GradingError(RuntimeError):
    """The run cannot grade, so it exits non-zero and writes no result."""


class _Invocation(NamedTuple):
    """The resolved roots, variant, and mode of one grader invocation."""

    student_root: Path
    result_path: Path
    variant: str
    classroom50_mode: bool


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    """Parse the bundle grader command line.

    ``--student-root`` and ``--result`` select the local dry run and are
    required as a pair; with neither the grader runs in Classroom 50 mode.

    Args:
        argv: Argument list to parse; ``sys.argv[1:]`` when omitted.

    Returns:
        The parsed namespace.

    Raises:
        SystemExit: On a usage error, including either local option supplied
            alone.
    """
    parser = argparse.ArgumentParser(
        description="Grade a student checkout with bundled hidden tests.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--student-root",
        type=Path,
        help="Local dry run: checkout whose notebooks and metadata are graded.",
    )
    parser.add_argument(
        "--result",
        type=Path,
        help="Local dry run: destination for the classroom50/result/v1 JSON payload.",
    )
    parser.add_argument(
        "--variant",
        choices=("student", "solution"),
        default="student",
        help="Local dry run notebook variant; solution is local dry-run only.",
    )
    args = parser.parse_args(argv)
    if (args.student_root is None) != (args.result is None):
        parser.error("--student-root and --result must be supplied together.")
    return args


def _resolve_invocation(args: Namespace) -> _Invocation:
    """Return the roots, result path, variant, and mode implied by the arguments."""
    if args.student_root is None:
        checkout = Path.cwd()
        return _Invocation(
            student_root=checkout,
            result_path=checkout / RESULT_FILENAME,
            variant="student",
            classroom50_mode=True,
        )
    return _Invocation(
        student_root=args.student_root,
        result_path=args.result,
        variant=args.variant,
        classroom50_mode=False,
    )


def _required_environment_value(
    environ: Mapping[str, str], name: str, *, fallback: str | None = None
) -> str:
    """Return the first non-empty value among a runner variable and its fallback.

    Args:
        environ: The environment the runner started the grader with.
        name: The documented runner variable name.
        fallback: An optional documented variable that also satisfies ``name``.

    Returns:
        The first non-empty value found.

    Raises:
        GradingError: Neither variable carries a value.
    """
    value = environ.get(name) or (environ.get(fallback) if fallback else None)
    if not value:
        expected = f"{name} or {fallback}" if fallback else name
        raise GradingError(f"Missing required environment value: {expected}.")
    return value


def read_runner_identity(environ: Mapping[str, str]) -> dict[str, str]:
    """Read the documented Classroom 50 identity from the runner environment.

    ``REVIEW_URL`` is optional and falls back to ``COMMIT_URL``; ``OWNER``
    falls back to ``USERNAME``. Unrelated runner variables are ignored.

    Args:
        environ: The environment Classroom 50 starts the grader with.

    Returns:
        The identity fields of the ``classroom50/result/v1`` payload.

    Raises:
        GradingError: A required value is missing, or the assignment type is
            unsupported.
    """
    values = {
        name: _required_environment_value(environ, name) for name in REQUIRED_RUNNER_VARIABLES
    }
    assignment_type = values["ASSIGNMENT_TYPE"]
    if assignment_type not in SUPPORTED_ASSIGNMENT_TYPES:
        raise GradingError(
            f"Unsupported ASSIGNMENT_TYPE {assignment_type!r}; expected one of "
            f"{', '.join(SUPPORTED_ASSIGNMENT_TYPES)}."
        )
    return {
        "classroom": values["CLASSROOM"],
        "assignment": values["ASSIGNMENT"],
        "assignment_type": assignment_type,
        "owner": _required_environment_value(environ, "OWNER", fallback="USERNAME"),
        "submission": values["SUBMISSION_TAG"],
        "commit": values["COMMIT_URL"],
        "release": values["RELEASE_URL"],
        "review": environ.get("REVIEW_URL") or values["COMMIT_URL"],
    }


def local_identity() -> dict[str, str]:
    """Return the documented non-uploadable identity of a local dry run."""
    return {
        "classroom": "local",
        "assignment": "local",
        "assignment_type": "individual",
        "owner": "local",
        "submission": "submit/local",
        "commit": "local://commit",
        "release": "local://release",
        "review": "local://review",
    }


def install_grading_dependencies() -> bool:
    """Install the grading dependencies into the grading interpreter.

    The install follows the ``pip`` pattern Classroom 50 documents for its own
    pytest autograder, and must complete before pytest is imported.

    Returns:
        ``True`` when the install succeeded, ``False`` when it failed.
    """
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", *GRADING_PACKAGES], check=False
    )
    if completed.returncode == 0:
        return True
    print(
        f"pip install of {', '.join(GRADING_PACKAGES)} failed with exit "
        f"{completed.returncode}; cannot grade.",
        file=sys.stderr,
    )
    return False


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

        Every phase counts, so a failing teardown turns an already passing call
        phase into a failed case.
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
    """Prepend the bundle to ``sys.path`` and expose the student checkout.

    The bundle ships its own ``exercise_runtime_support`` copy, so it must
    come first; ``exercise_metadata`` ships only in the student checkout, so
    the checkout follows right behind it.
    """
    for entry in (str(student_root), str(bundle_root)):
        while entry in sys.path:
            sys.path.remove(entry)
    sys.path.insert(0, str(bundle_root))
    sys.path.insert(1, str(student_root))


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
        raise RuntimeError(
            "exercise_runtime_support resolved to "
            f"{runtime_dir}, not the bundle copy under {bundle_root}."
        )
    if metadata_dir.parent != student_root:
        raise RuntimeError(
            "exercise_metadata resolved to "
            f"{metadata_dir}, not the student checkout under {student_root}."
        )


def build_result_payload(
    collector: _OutcomeCollector, identity: dict[str, str]
) -> dict[str, object]:
    """Build the ``classroom50/result/v1`` payload from collected outcomes.

    Args:
        collector: The collected per-case outcomes of the graded run.
        identity: The identity fields for the invocation's mode.

    Returns:
        The result document, awarding one point per passing case.
    """
    entries: list[dict[str, object]] = []
    total = 0
    for nodeid in collector.nodeids:
        exercise_key = _exercise_key_for_nodeid(nodeid, collector.exercise_keys)
        passed = collector.statuses.get(nodeid) == "passed"
        entries.append(
            {
                "test-name": f"{exercise_key}::{_leaf_name(nodeid)}",
                "passed": passed,
                "score": int(passed),
                "max-score": 1,
            }
        )
        total += int(passed)
    return {
        "schema": RESULT_SCHEMA,
        **identity,
        "datetime": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "score": total,
        "max-score": len(entries),
        "tests": entries,
    }


def invalidate_result(result_path: Path) -> None:
    """Remove any pre-existing result output before a grading attempt."""
    result_path.unlink(missing_ok=True)


def run_bundle(
    bundle_root: Path, student_root: Path, variant: str, identity: dict[str, str]
) -> tuple[dict[str, object] | None, int]:
    """Grade the checkout and return the payload plus the process exit code.

    Completed pytest runs (exits 0 and 1) return a payload with exit 0.
    Infrastructure failures (any other pytest exit, or no hidden tests at all)
    return no payload with a non-zero exit. The caller removes any
    pre-existing result output beforehand, so nothing stale remains.

    pytest is imported here so a Classroom 50 mode install always completes
    before the first import.
    """
    import pytest

    os.environ[ACTIVE_VARIANT_ENV_VAR] = variant
    student_root = student_root.resolve()
    configure_bundle_paths(bundle_root, student_root)
    _check_package_origins(bundle_root, student_root)
    test_files = discover_hidden_tests(bundle_root)
    if not test_files:
        print("No bundled hidden tests found; cannot grade.", file=sys.stderr)
        return None, 2
    collector = _OutcomeCollector()
    pytest_exit = int(
        pytest.main(
            [str(path) for path in test_files] + ["-q", "-p", "no:cacheprovider"],
            plugins=[collector],
        )
    )
    if pytest_exit in (0, 1):
        return build_result_payload(collector, identity), 0
    print(
        f"pytest exited with {pytest_exit}; infrastructure error, no grade written.",
        file=sys.stderr,
    )
    return None, pytest_exit


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bundle grader and write the result document for completed runs."""
    args = parse_args(argv)
    invocation = _resolve_invocation(args)
    invalidate_result(invocation.result_path)
    if invocation.classroom50_mode:
        if not install_grading_dependencies():
            return 2
        try:
            identity = read_runner_identity(os.environ)
        except GradingError as error:
            print(str(error), file=sys.stderr)
            return 2
    else:
        identity = local_identity()
    if not invocation.student_root.is_dir():
        print(f"Student checkout not found: {invocation.student_root}", file=sys.stderr)
        return 2
    payload, exit_code = run_bundle(
        Path(__file__).resolve().parent, invocation.student_root, invocation.variant, identity
    )
    if payload is None:
        return exit_code
    invocation.result_path.parent.mkdir(parents=True, exist_ok=True)
    invocation.result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
