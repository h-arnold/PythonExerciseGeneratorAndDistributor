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
``<bundle>/exercise_runtime_support/`` from the current runtime source.

Four target contract files land in the bundle root in one stage, after every
selected hidden file and the runtime copy are in place and before the grader
itself is copied:

* ``requirements.txt``, ``pytest.ini``, and ``classroom50_manifest.py`` are
  byte-for-byte copies of their committed ``scripts/`` sources, so the bundle
  can install a lock-derived dependency set and grade with trusted configuration;
* ``grading_manifest.json`` is the closed ``classroom50/grading-manifest/v1``
  document for the selected records, written only after the shared validator in
  ``scripts/classroom50_manifest.py`` has accepted it against the populated
  bundle.

The bundle therefore either carries all four files or carries none of them, and
never carries a grader that would bootstrap from a half-written contract.

No classroom operation is implied or performed; this is a local build only.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from argparse import Namespace
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, cast

from scripts.classroom50_manifest import (
    GRADING_MANIFEST_FILENAME,
    ExerciseRecord,
    build_manifest,
    canonical_test_path,
    validate_manifest,
)

SCRIPTS_ROOT: Final[Path] = Path(__file__).resolve().parent
GRADER_FILENAME: Final[str] = "autograder.py"

# The fixed source-to-target mapping for the three copied contract files. The
# manifest document is generated rather than copied, and the grader is copied last.
COPIED_CONTRACT_SOURCES: Final[Mapping[str, Path]] = MappingProxyType(
    {
        "requirements.txt": SCRIPTS_ROOT / "classroom50_requirements.txt",
        "pytest.ini": SCRIPTS_ROOT / "classroom50_pytest.ini",
        "classroom50_manifest.py": SCRIPTS_ROOT / "classroom50_manifest.py",
    }
)
GRADER_SOURCE: Final[Path] = SCRIPTS_ROOT / GRADER_FILENAME

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


def _hidden_test_modules(source_tests: Path) -> list[str]:
    """Return the sorted ``test_*.py`` module names in one canonical tests directory."""
    return sorted(
        path.name
        for path in source_tests.iterdir()
        if path.is_file() and path.name.startswith("test_") and path.suffix == ".py"
    )


def _manifest_test_filename(
    source_tests: Path, exercise_key: str, candidates: Sequence[str]
) -> str:
    """Return the hidden test module the grading manifest names for one exercise.

    The canonical module is ``tests/test_<exercise_key>.py``. A later stage makes
    that exact name mandatory; until then an exercise whose canonical tests
    directory holds exactly one ``test_*.py`` module is also accepted, and
    anything ambiguous - including no module at all - fails the build rather than
    guessing.

    Args:
        source_tests: The exercise's canonical ``tests`` directory in the source tree.
        exercise_key: Canonical identity of the selected exercise.
        candidates: The ``test_*.py`` module names already found in ``source_tests``.

    Returns:
        The hidden test module filename to record in the manifest.

    Raises:
        FileNotFoundError: If no single hidden test module can be named.
    """
    canonical = f"test_{exercise_key}.py"
    if canonical in candidates:
        return canonical
    if len(candidates) == 1:
        return candidates[0]
    raise FileNotFoundError(
        f"Expected exactly one hidden test module for {exercise_key!r} in {source_tests}; "
        f"found {list(candidates)}."
    )


def _collect_required_filenames(source_tests: Path, test_names: Sequence[str]) -> list[str]:
    """Return every hidden filename one exercise tests directory must contribute.

    ``test_names`` is the already-resolved ``test_*.py`` set, so the caller names
    the graded module exactly once and no empty case can reach this function.
    """
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
) -> ExerciseRecord:
    """Copy one exercise's required hidden grading files and return its manifest record.

    Args:
        source_root: Root of the canonical exercise source tree.
        construct: Construct directory name to select.
        exercise_key: Canonical identity of the selected exercise.
        bundle_root: Bundle root that receives the hidden files.

    Returns:
        The manifest record naming the exercise's bundled hidden test module.
    """
    source_tests = source_root / "exercises" / construct / exercise_key / "tests"
    if not source_tests.is_dir():
        raise FileNotFoundError(f"Canonical tests directory not found: {source_tests}")
    test_names = _hidden_test_modules(source_tests)
    filename = _manifest_test_filename(source_tests, exercise_key, test_names)
    target_tests = bundle_root / "exercises" / construct / exercise_key / "tests"
    target_tests.mkdir(parents=True, exist_ok=True)
    for name in _collect_required_filenames(source_tests, test_names):
        source_file = source_tests / name
        if not source_file.is_file():
            raise FileNotFoundError(
                f"Required hidden file {name!r} not found for {exercise_key!r}."
            )
        shutil.copy2(source_file, target_tests / name)
    return {
        "construct": construct,
        "exercise_key": exercise_key,
        "test_path": canonical_test_path(construct, exercise_key, filename),
    }


def _require_bundle_sources() -> None:
    """Fail fast when a committed source the bundle copies is missing."""
    sources = {**COPIED_CONTRACT_SOURCES, GRADER_FILENAME: GRADER_SOURCE}
    missing = sorted(name for name, source in sources.items() if not source.is_file())
    if missing:
        raise FileNotFoundError(f"Committed bundle sources are missing: {missing}.")


def _emit_target_contract(bundle_root: Path, records: Sequence[ExerciseRecord]) -> None:
    """Emit the four target contract files after validating the manifest.

    The manifest is validated against the populated bundle before anything is
    written, so a target either carries a manifest whose test paths resolve inside
    it or carries no manifest at all.

    Args:
        bundle_root: Bundle root that receives the contract files.
        records: The validated-in-order manifest records for the selected exercises.
    """
    manifest = build_manifest(records)
    validate_manifest(manifest, bundle_root=bundle_root)
    for name, source in COPIED_CONTRACT_SOURCES.items():
        shutil.copy2(source, bundle_root / name)
    (bundle_root / GRADING_MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def build_bundle(
    source_root: Path,
    records: list[tuple[str, str]],
    runtime_source: Path,
    output: Path,
) -> Path:
    """Assemble the bundle directory and return its path.

    The hidden tests and the bundle-local runtime copy land first, then the four
    target contract files in one stage, and only then the grader itself: a bundle
    that carries ``autograder.py`` therefore always carries the requirements,
    configuration, shared validator, and manifest its native run needs.

    Args:
        source_root: Root of the canonical exercise source tree.
        records: The selected ``(construct, exercise_key)`` records.
        runtime_source: Current ``exercise_runtime_support`` package source.
        output: Bundle directory to create.

    Returns:
        The bundle root that was populated.
    """
    if not runtime_source.is_dir():
        raise FileNotFoundError(f"Runtime source not found: {runtime_source}")
    _require_bundle_sources()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest_records = [
        copy_hidden_tests(source_root, construct, exercise_key, output)
        for construct, exercise_key in records
    ]
    shutil.copytree(
        runtime_source,
        output / "exercise_runtime_support",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    _emit_target_contract(output, manifest_records)
    shutil.copy2(GRADER_SOURCE, output / GRADER_FILENAME)
    return output


def main(argv: Sequence[str] | None = None) -> int:
    """Build the bundle and return a process exit code."""
    args = parse_args(argv)
    records = load_exercise_set(Path(args.exercise_set))
    build_bundle(Path(args.source_root), records, Path(args.runtime_source), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
