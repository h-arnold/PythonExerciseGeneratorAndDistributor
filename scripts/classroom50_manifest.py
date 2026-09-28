"""Shared ``classroom50/grading-manifest/v1`` wire format and validator.

``scripts/build_classroom50_bundle.py`` copies this module into the bundle root
next to the ``grading_manifest.json`` it writes, so the builder and the
bundle-local ``autograder.py`` validate the document against one shared
definition instead of two restatements of the same format.  The module is
standard-library only and reads nothing outside the bundle root it is handed:
the bundle carries it verbatim, so a student checkout cannot substitute it.

The contract validated here is the minimum closed shape: exactly ``schema`` and
``exercises``, one record per selected exercise holding exactly ``construct``,
``exercise_key``, and ``test_path``, POSIX bundle-relative paths that resolve to
a file beneath the bundle root, and records sorted by ``(construct, exercise_key)``
with unique exercise identities and unique test paths.  The support-module
closure, exercise-identity validation against ``exercise.json``, and the
canonical ``test_<exercise_key>.py`` filename rule are added by a later stage;
the checks below already reject every missing, duplicate, malformed,
non-canonical, or out-of-bundle entry.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final, TypedDict, TypeGuard, cast

GRADING_MANIFEST_SCHEMA: Final[str] = "classroom50/grading-manifest/v1"
GRADING_MANIFEST_FILENAME: Final[str] = "grading_manifest.json"
MANIFEST_FIELDS: Final[tuple[str, ...]] = ("schema", "exercises")
EXERCISE_RECORD_FIELDS: Final[tuple[str, ...]] = ("construct", "exercise_key", "test_path")
HIDDEN_TESTS_DIRNAME: Final[str] = "tests"
EXERCISES_DIRNAME: Final[str] = "exercises"


class ManifestError(ValueError):
    """Raised when a grading manifest violates the closed wire contract."""


class ExerciseRecord(TypedDict):
    """One manifest entry naming the graded hidden test module of one exercise."""

    construct: str
    exercise_key: str
    test_path: str


def is_str_mapping(value: object) -> TypeGuard[dict[str, Any]]:
    """Return True when ``value`` is a JSON object with string keys."""
    if not isinstance(value, dict):
        return False
    entries = cast("dict[object, object]", value)
    return all(isinstance(key, str) for key in entries)


def is_exercise_record(value: object) -> TypeGuard[ExerciseRecord]:
    """Return True when ``value`` holds exactly the three non-empty record fields."""
    if not is_str_mapping(value) or set(value) != set(EXERCISE_RECORD_FIELDS):
        return False
    return all(isinstance(value[field], str) and value[field] for field in EXERCISE_RECORD_FIELDS)


def canonical_test_path(construct: str, exercise_key: str, filename: str) -> str:
    """Return the canonical bundle-relative POSIX path of an exercise's test module.

    Args:
        construct: Construct directory name the exercise lives under.
        exercise_key: Canonical exercise identity.
        filename: Hidden test module filename inside the exercise's tests directory.

    Returns:
        The POSIX bundle-relative path, for example
        ``exercises/sequence/ex001_x/tests/test_ex001_x.py``.
    """
    return f"{EXERCISES_DIRNAME}/{construct}/{exercise_key}/{HIDDEN_TESTS_DIRNAME}/{filename}"


def build_manifest(records: Sequence[ExerciseRecord]) -> dict[str, Any]:
    """Return the closed grading-manifest document for ``records``.

    Args:
        records: The selected exercise records the bundle grades.

    Returns:
        A JSON-ready document with the records in canonical sorted order.
    """
    ordered = sorted(records, key=lambda record: (record["construct"], record["exercise_key"]))
    return {
        "schema": GRADING_MANIFEST_SCHEMA,
        "exercises": [dict(record) for record in ordered],
    }


def validate_manifest(manifest: object, *, bundle_root: Path) -> list[ExerciseRecord]:
    """Return the manifest's exercise records once the closed contract holds.

    Args:
        manifest: The parsed grading manifest document.
        bundle_root: Bundle root every ``test_path`` must resolve beneath.

    Returns:
        The validated records in document order.

    Raises:
        ManifestError: If the document, a record, or a test path is malformed,
            duplicated, non-canonical, or resolves outside the bundle.
    """
    if not is_str_mapping(manifest):
        raise ManifestError(
            f"The grading manifest must be a JSON object; got {type(manifest).__name__}."
        )
    if set(manifest) != set(MANIFEST_FIELDS):
        raise ManifestError(
            f"The grading manifest must hold exactly {list(MANIFEST_FIELDS)}; "
            f"got {sorted(manifest)}."
        )
    if manifest["schema"] != GRADING_MANIFEST_SCHEMA:
        raise ManifestError(
            f"The grading manifest schema must be {GRADING_MANIFEST_SCHEMA!r}; "
            f"got {manifest['schema']!r}."
        )
    exercises: Any = manifest["exercises"]
    if not isinstance(exercises, list) or not exercises:
        raise ManifestError(
            f"The grading manifest must list at least one exercise record; got {exercises!r}."
        )
    entries = cast("list[object]", exercises)
    records = [_validated_record(entry, bundle_root=bundle_root) for entry in entries]
    _require_sorted_unique(records)
    return records


def _validated_record(entry: object, *, bundle_root: Path) -> ExerciseRecord:
    """Return one validated exercise record, or fail naming the offending entry."""
    if not is_exercise_record(entry):
        raise ManifestError(
            "Every manifest exercise record must hold exactly "
            f"{list(EXERCISE_RECORD_FIELDS)} non-empty strings; got {entry!r}."
        )
    return {
        "construct": entry["construct"],
        "exercise_key": entry["exercise_key"],
        "test_path": _validated_test_path(entry["test_path"], bundle_root=bundle_root),
    }


def _validated_test_path(raw: str, *, bundle_root: Path) -> str:
    """Return ``raw`` when it is a canonical bundle-relative path to a bundled file."""
    _require_canonical_relative_path(raw)
    root = bundle_root.resolve()
    resolved = (root / raw).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ManifestError(
            f"Manifest test_path {raw!r} must resolve to a file beneath the bundle root {root}."
        )
    return raw


def _require_canonical_relative_path(raw: str) -> None:
    """Fail unless ``raw`` is a relative POSIX path with no empty, ``.`` or ``..`` segment."""
    if "\\" in raw:
        raise ManifestError(f"Manifest test_path {raw!r} must use POSIX '/' separators.")
    unusable = ("", ".", "..")
    if any(segment in unusable for segment in raw.split("/")):
        raise ManifestError(
            f"Manifest test_path {raw!r} must be bundle-relative with no empty, "
            "'.' or '..' segment."
        )


def _require_sorted_unique(records: Sequence[ExerciseRecord]) -> None:
    """Fail unless identities are unique and sorted and test paths are unique."""
    identities = [(record["construct"], record["exercise_key"]) for record in records]
    if len(set(identities)) != len(identities):
        raise ManifestError(f"Manifest exercise identities must be unique; got {identities}.")
    if list(identities) != sorted(identities):
        raise ManifestError(
            "Manifest exercise records must be sorted by (construct, exercise_key); "
            f"got {[f'{construct}/{key}' for construct, key in identities]}."
        )
    test_paths = [record["test_path"] for record in records]
    if len(set(test_paths)) != len(test_paths):
        raise ManifestError(f"Manifest test_path values must be unique; got {test_paths}.")
