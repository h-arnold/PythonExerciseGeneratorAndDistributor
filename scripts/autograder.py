"""Generic Classroom 50 grader for teacher-side assignment bundles.

The bundle directory holding this script is the discovery root: hidden tests
are collected from ``<bundle>/exercises/<construct>/<exercise_key>/tests/``
only, never from the student checkout. The bundle root is prepended to
``sys.path`` so exercise-local support modules resolve into the bundle, while
``exercise_metadata`` resolves from the student checkout so notebooks resolve
to student work.

The graded run always forces ``PYTUTOR_ACTIVE_VARIANT=student``. ``--variant
solution`` exists for the local dry run only.

Exit semantics follow the documented contract: pytest outcomes 0 (all passed)
and 1 (tests ran and some failed) are completed runs, so the grader writes the
``classroom50/result/v1`` payload and exits 0 with pass/fail carried in the
payload. Any other pytest exit (interrupted collection, internal or usage
error, no tests collected) — or an empty discovery set — is an infrastructure
error: the grader exits non-zero and writes no completed payload. Any
pre-existing result output is removed before the grading attempt, so a stale
result file can never survive an infrastructure failure and be misread as a
grade.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from argparse import Namespace
from collections.abc import Sequence
from pathlib import Path

import pytest

RESULT_VERSION = "classroom50/result/v1"
ACTIVE_VARIANT_ENV_VAR = "PYTUTOR_ACTIVE_VARIANT"


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    """Parse the bundle grader command line."""
    parser = argparse.ArgumentParser(
        description="Grade a student checkout with bundled hidden tests.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--student-root",
        required=True,
        type=Path,
        help="Checkout whose notebooks and metadata are graded.",
    )
    parser.add_argument(
        "--result",
        required=True,
        type=Path,
        help="Destination path for the classroom50/result/v1 JSON payload.",
    )
    parser.add_argument(
        "--variant",
        choices=("student", "solution"),
        default="student",
        help="Notebook variant to expose; solution is local dry-run only.",
    )
    return parser.parse_args(argv)


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
        """Record the terminal outcome for a single report phase."""
        if report.when == "teardown":
            return
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


def build_result_payload(collector: _OutcomeCollector) -> dict[str, object]:
    """Build the classroom50/result/v1 payload from collected outcomes."""
    entries: list[dict[str, object]] = []
    total = 0
    for nodeid in collector.nodeids:
        name = f"{_exercise_key_for_nodeid(nodeid, collector.exercise_keys)}::{_leaf_name(nodeid)}"
        score = 1 if collector.statuses.get(nodeid) == "passed" else 0
        entries.append({"name": name, "score": score, "max-score": 1})
        total += score
    return {
        "version": RESULT_VERSION,
        "score": total,
        "max-score": len(entries),
        "tests": entries,
    }


def invalidate_result(result_path: Path) -> None:
    """Remove any pre-existing result output before a grading attempt."""
    result_path.unlink(missing_ok=True)


def run_bundle(
    bundle_root: Path, student_root: Path, variant: str
) -> tuple[dict[str, object] | None, int]:
    """Grade the checkout and return the payload plus the process exit code.

    Completed pytest runs (exits 0 and 1) return a payload with exit 0.
    Infrastructure failures (any other pytest exit, or no hidden tests at all)
    return no payload with a non-zero exit. The caller removes any
    pre-existing result output beforehand, so nothing stale remains.
    """
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
        return build_result_payload(collector), 0
    print(
        f"pytest exited with {pytest_exit}; infrastructure error, no grade written.",
        file=sys.stderr,
    )
    return None, pytest_exit


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bundle grader and write ``result.json`` for completed runs."""
    args = parse_args(argv)
    bundle_root = Path(__file__).resolve().parent
    student_root = Path(args.student_root)
    result_path = Path(args.result)
    invalidate_result(result_path)
    if not student_root.is_dir():
        print(f"Student checkout not found: {student_root}", file=sys.stderr)
        return 2
    payload, exit_code = run_bundle(bundle_root, student_root, args.variant)
    if payload is None:
        return exit_code
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
