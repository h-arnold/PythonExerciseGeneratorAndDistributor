"""Build a teacher-side Classroom 50 grading bundle from a chosen exercise set.

The exercise set is a JSON list of ``{"construct": ..., "exercise_key": ...}``
records. For each record the builder copies only the required hidden grading
files from the source tree into
``<bundle>/exercises/<construct>/<exercise_key>/tests/``: ``test_*.py``
modules, the documented support modules, and any further local support module
referenced through ``load_exercise_test_module`` (resolved transitively, so
exercise-local helpers stay available without naming them here). Anything else
stays out of the bundle: notebooks, solutions, metadata, teacher notes, and
unrelated or non-Python files are never copied. The builder also regenerates
``<bundle>/exercise_runtime_support/`` from the current runtime source and
copies this directory's ``autograder.py`` to the bundle root.

No classroom operation is implied or performed; this is a local build only.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from argparse import Namespace
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

DOCUMENTED_SUPPORT_MODULES = ("expectations.py", "student_checker_support.py")

_LOAD_MODULE_PATTERN = re.compile(
    r"load_exercise_test_module\s*\(\s*[^,]+,\s*[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']",
    re.DOTALL,
)


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    """Parse the bundle builder command line."""
    parser = argparse.ArgumentParser(
        description="Assemble a Classroom 50 grading bundle from chosen exercises.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source-root",
        required=True,
        type=Path,
        help="Exercise source tree holding the chosen exercise tests.",
    )
    parser.add_argument(
        "--exercise-set",
        required=True,
        type=Path,
        help="JSON list of {construct, exercise_key} records to bundle.",
    )
    parser.add_argument(
        "--runtime-source",
        required=True,
        type=Path,
        help="Current exercise_runtime_support package source to copy.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Teacher-side bundle directory to create.",
    )
    return parser.parse_args(argv)


def load_exercise_set(exercise_set_path: Path) -> list[tuple[str, str]]:
    """Load and validate the chosen ``(construct, exercise_key)`` records."""
    raw: Any = json.loads(exercise_set_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Exercise set at {exercise_set_path} must be a JSON list.")
    records: list[tuple[str, str]] = []
    for entry in cast("list[Any]", raw):
        if not isinstance(entry, dict):
            raise ValueError(f"Exercise set record {entry!r} must be an object.")
        fields = cast("dict[str, Any]", entry)
        construct = fields.get("construct")
        exercise_key = fields.get("exercise_key")
        if not isinstance(construct, str) or not construct:
            raise ValueError(f"Exercise set record {entry!r} has an invalid construct.")
        if not isinstance(exercise_key, str) or not exercise_key:
            raise ValueError(f"Exercise set record {entry!r} has an invalid exercise_key.")
        records.append((construct, exercise_key))
    return records


def _referenced_support_modules(source_text: str) -> set[str]:
    """Return support module names referenced via load_exercise_test_module."""
    return set(_LOAD_MODULE_PATTERN.findall(source_text))


def _collect_required_filenames(source_tests: Path) -> list[str]:
    """Return the required hidden filenames for one exercise tests directory."""
    test_names = sorted(
        path.name
        for path in source_tests.iterdir()
        if path.is_file() and path.name.startswith("test_") and path.suffix == ".py"
    )
    if not test_names:
        raise FileNotFoundError(f"No hidden test files found in {source_tests}.")
    required = set(test_names) | set(DOCUMENTED_SUPPORT_MODULES)
    queue = sorted(required)
    scanned: set[str] = set()
    while queue:
        name = queue.pop()
        if name in scanned:
            continue
        scanned.add(name)
        candidate = source_tests / name
        if candidate.is_file():
            for module in _referenced_support_modules(candidate.read_text(encoding="utf-8")):
                module_file = f"{module}.py"
                if module_file not in required:
                    required.add(module_file)
                    queue.append(module_file)
    return sorted(required)


def copy_hidden_tests(
    source_root: Path, construct: str, exercise_key: str, bundle_root: Path
) -> None:
    """Copy one exercise's required hidden grading files into the bundle."""
    source_tests = source_root / "exercises" / construct / exercise_key / "tests"
    if not source_tests.is_dir():
        raise FileNotFoundError(f"Canonical tests directory not found: {source_tests}")
    target_tests = bundle_root / "exercises" / construct / exercise_key / "tests"
    target_tests.mkdir(parents=True, exist_ok=True)
    for name in _collect_required_filenames(source_tests):
        source_file = source_tests / name
        if not source_file.is_file():
            raise FileNotFoundError(
                f"Required hidden file {name!r} not found for {exercise_key!r}."
            )
        shutil.copy2(source_file, target_tests / name)


def build_bundle(
    source_root: Path,
    records: list[tuple[str, str]],
    runtime_source: Path,
    output: Path,
) -> Path:
    """Assemble the bundle directory and return its path."""
    if not runtime_source.is_dir():
        raise FileNotFoundError(f"Runtime source not found: {runtime_source}")
    grader_source = Path(__file__).resolve().parent / "autograder.py"
    if not grader_source.is_file():
        raise FileNotFoundError(f"Grader source not found: {grader_source}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    for construct, exercise_key in records:
        copy_hidden_tests(source_root, construct, exercise_key, output)
    shutil.copytree(
        runtime_source,
        output / "exercise_runtime_support",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy2(grader_source, output / "autograder.py")
    return output


def main(argv: Sequence[str] | None = None) -> int:
    """Build the bundle and return a process exit code."""
    args = parse_args(argv)
    records = load_exercise_set(Path(args.exercise_set))
    build_bundle(Path(args.source_root), records, Path(args.runtime_source), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
