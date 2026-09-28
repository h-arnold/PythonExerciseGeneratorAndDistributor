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

Exit semantics follow the documented contract: pytest outcomes 0 (all passed)
and 1 (tests ran and some failed) are completed runs, so the grader writes the
``classroom50/result/v1`` payload and exits 0 with pass/fail carried in the
payload. Any other pytest exit (interrupted collection, internal or usage
error, no tests collected) — or an empty discovery set — is an infrastructure
error: the grader exits non-zero and writes no completed payload. A missing or
invalid native environment is reported the same way. Any pre-existing result
output is removed before the grading attempt, so a stale result file can never
survive an infrastructure failure and be misread as a grade.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from argparse import Namespace
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

RESULT_SCHEMA: Final[str] = "classroom50/result/v1"
ACTIVE_VARIANT_ENV_VAR: Final[str] = "PYTUTOR_ACTIVE_VARIANT"
BUNDLE_DIR_ENV_VAR: Final[str] = "CLASSROOM50_BUNDLE_DIR"
NATIVE_RESULT_FILENAME: Final[str] = "result.json"
ASSIGNMENT_TYPE_ENV_VAR: Final[str] = "ASSIGNMENT_TYPE"
SUPPORTED_ASSIGNMENT_TYPES: Final[tuple[str, ...]] = ("individual", "group", "team")
OWNER_ENV_VARS: Final[tuple[str, ...]] = ("OWNER", "USERNAME")
DATETIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"

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


class GradingConfigurationError(RuntimeError):
    """Raised when an invocation or the native environment cannot be graded."""


@dataclass(frozen=True)
class GradingRequest:
    """One resolved grading request: the roots, the variant, and the result identity."""

    bundle_root: Path
    student_root: Path
    variant: str
    identity: Mapping[str, str]


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
    )


def _native_grading_request() -> GradingRequest:
    """Return the request the Classroom 50 runner implies with no arguments."""
    return GradingRequest(
        bundle_root=Path(_required_native_value(BUNDLE_DIR_ENV_VAR)).resolve(),
        student_root=Path.cwd(),
        variant="student",
        identity=_native_identity(),
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


def _run_pytest(test_files: list[str], collector: _OutcomeCollector) -> int:
    """Return pytest's exit code for the bundled hidden tests.

    This is the only pytest invocation in the module, so the native dependency
    bootstrap can own the import and the environment it runs in.
    """
    return int(
        pytest.main(
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
    _check_package_origins(request.bundle_root, student_root)
    test_files = discover_hidden_tests(request.bundle_root)
    if not test_files:
        print("No bundled hidden tests found; cannot grade.", file=sys.stderr)
        return None, 2
    collector = _OutcomeCollector()
    pytest_exit = _run_pytest([str(path) for path in test_files], collector)
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
    payload, exit_code = run_bundle(request)
    if payload is None:
        return exit_code
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
