#!/usr/bin/env python3
"""One-off migration helper for canonical exercise directories.

This script migrates legacy notebook files and shadow exercise homes into the
canonical layout under ``exercises/<construct>/<exercise_key>/``.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_FILENAMES = ("README.md", "OVERVIEW.md", "solutions.md")
LEGACY_EXERCISE_TYPES = ("debug", "make", "modify")
MANIFEST_PATH = Path("exercises") / "migration_manifest.json"


class MigrationError(RuntimeError):
    """Raised when the migration plan cannot be built safely."""


class MigrationConflictError(MigrationError):
    """Raised when a canonical destination already exists with different content."""


@dataclass(frozen=True)
class ExerciseRecord:
    """Canonical exercise metadata required for migration."""

    exercise_key: str
    construct: str
    exercise_type: str
    canonical_dir: Path
    shadow_dir: Path | None


@dataclass(frozen=True)
class Action:
    """A filesystem or content change that can be reported and optionally applied."""

    kind: str
    description: str
    source: Path | None = None
    destination: Path | None = None
    content: str | None = None


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Move legacy notebooks and shadow exercise assets into canonical "
            "exercise directories for one construct."
        )
    )
    parser.add_argument(
        "--construct",
        required=True,
        help="Construct to migrate, for example 'sequence'.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Repository root to inspect. Defaults to the current repository.",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        dest="apply",
        action="store_false",
        help="Preview the migration plan without changing files (default).",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Apply the migration plan.",
    )
    parser.set_defaults(apply=False)
    return parser.parse_args(argv)


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MigrationError(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MigrationError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise MigrationError(f"Expected a JSON object in {path}")
    return data


def _relative_to_repo(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _files_match(source: Path, destination: Path) -> bool:
    return source.read_bytes() == destination.read_bytes()


def _load_exercise_record(
    exercise_dir: Path,
    *,
    construct: str,
    repo_root: Path,
) -> ExerciseRecord:
    metadata = _load_json_object(exercise_dir / "exercise.json")

    exercise_key = metadata.get("exercise_key")
    if not isinstance(exercise_key, str) or exercise_key != exercise_dir.name:
        raise MigrationError(
            f"Canonical exercise metadata must define exercise_key={exercise_dir.name!r} "
            f"in {exercise_dir / 'exercise.json'}"
        )

    metadata_construct = metadata.get("construct")
    if not isinstance(metadata_construct, str) or metadata_construct != construct:
        raise MigrationError(
            f"Canonical exercise metadata in {exercise_dir / 'exercise.json'} must define "
            f"construct={construct!r}"
        )

    exercise_type = metadata.get("exercise_type")
    if not isinstance(exercise_type, str) or exercise_type not in LEGACY_EXERCISE_TYPES:
        raise MigrationError(
            f"Canonical exercise metadata in {exercise_dir / 'exercise.json'} must define a "
            "valid exercise_type"
        )

    shadow_dir = repo_root / "exercises" / construct / exercise_type / exercise_key
    return ExerciseRecord(
        exercise_key=exercise_key,
        construct=construct,
        exercise_type=exercise_type,
        canonical_dir=exercise_dir,
        shadow_dir=shadow_dir if shadow_dir.is_dir() else None,
    )


def _discover_exercises(repo_root: Path, construct: str) -> list[ExerciseRecord]:
    construct_dir = repo_root / "exercises" / construct
    if not construct_dir.is_dir():
        raise MigrationError(f"Construct directory not found: {construct_dir}")

    exercises: list[ExerciseRecord] = []
    for path in sorted(construct_dir.iterdir()):
        if not path.is_dir():
            continue
        if path.name in LEGACY_EXERCISE_TYPES or path.name == "__pycache__":
            continue
        if not (path / "exercise.json").is_file():
            continue
        exercises.append(_load_exercise_record(
            path, construct=construct, repo_root=repo_root))

    if not exercises:
        raise MigrationError(
            f"No canonical exercise directories found for construct {construct!r}")
    return exercises


def _plan_file_transfer(source: Path, destination: Path, repo_root: Path) -> list[Action]:
    if not source.is_file():
        return []

    if destination.exists():
        if not destination.is_file():
            raise MigrationConflictError(
                f"Conflict: {_relative_to_repo(destination, repo_root)} exists but is not a file"
            )
        if _files_match(source, destination):
            return [
                Action(
                    kind="remove_file",
                    description=(
                        f"remove duplicate legacy file {_relative_to_repo(source, repo_root)}"
                    ),
                    source=source,
                )
            ]
        raise MigrationConflictError(
            "Conflict: "
            f"{_relative_to_repo(destination, repo_root)} already exists and differs from "
            f"{_relative_to_repo(source, repo_root)}"
        )

    return [
        Action(
            kind="move_file",
            description=(
                f"move {_relative_to_repo(source, repo_root)} -> "
                f"{_relative_to_repo(destination, repo_root)}"
            ),
            source=source,
            destination=destination,
        )
    ]


def _plan_required_notebook_transfer(
    source: Path,
    destination: Path,
    repo_root: Path,
    *,
    exercise_key: str,
    notebook_role: str,
) -> list[Action]:
    if source.is_file():
        return _plan_file_transfer(source, destination, repo_root)

    if destination.exists():
        if not destination.is_file():
            raise MigrationConflictError(
                f"Conflict: {_relative_to_repo(destination, repo_root)} exists but is not a file"
            )
        return []

    raise MigrationError(
        f"Missing required {notebook_role} notebook for {exercise_key}: neither "
        f"{_relative_to_repo(source, repo_root)} nor "
        f"{_relative_to_repo(destination, repo_root)} exists"
    )


def _plan_notebook_actions(record: ExerciseRecord, repo_root: Path) -> list[Action]:
    actions: list[Action] = []
    notebook_pairs = (
        (
            "student",
            repo_root / "notebooks" / f"{record.exercise_key}.ipynb",
            record.canonical_dir / "notebooks" / "student.ipynb",
        ),
        (
            "solution",
            repo_root / "notebooks" / "solutions" /
            f"{record.exercise_key}.ipynb",
            record.canonical_dir / "notebooks" / "solution.ipynb",
        ),
    )

    for notebook_role, source, destination in notebook_pairs:
        actions.extend(
            _plan_required_notebook_transfer(
                source,
                destination,
                repo_root,
                exercise_key=record.exercise_key,
                notebook_role=notebook_role,
            )
        )
    return actions


def _plan_retry_safe_shadow_doc_cleanup(
    record: ExerciseRecord,
    source: Path,
    destination: Path,
    repo_root: Path,
) -> list[Action] | None:
    if record.shadow_dir is None:
        return None

    relative_source = source.relative_to(record.shadow_dir)
    if relative_source.parent != Path(".") or relative_source.name not in DOC_FILENAMES:
        return None
    if not destination.is_file():
        return None

    source_text = source.read_text(encoding="utf-8")
    rewritten_text = _rewrite_exercise_doc(source_text, record)
    if destination.read_text(encoding="utf-8") != rewritten_text:
        return None

    return [
        Action(
            kind="remove_file",
            description=(
                "remove legacy shadow file "
                f"{_relative_to_repo(source, repo_root)} because an equivalent canonical "
                "doc already exists"
            ),
            source=source,
        )
    ]


def _plan_shadow_actions(record: ExerciseRecord, repo_root: Path) -> list[Action]:
    if record.shadow_dir is None:
        return []

    actions: list[Action] = []
    for source in sorted(path for path in record.shadow_dir.rglob("*") if path.is_file()):
        destination = record.canonical_dir / \
            source.relative_to(record.shadow_dir)
        retry_safe_cleanup = _plan_retry_safe_shadow_doc_cleanup(
            record,
            source,
            destination,
            repo_root,
        )
        if retry_safe_cleanup is not None:
            actions.extend(retry_safe_cleanup)
            continue
        actions.extend(_plan_file_transfer(source, destination, repo_root))

    actions.append(
        Action(
            kind="cleanup_dir",
            description=(
                f"remove empty legacy directory {_relative_to_repo(record.shadow_dir, repo_root)}"
            ),
            source=record.shadow_dir,
        )
    )
    return actions


def _existing_doc_text(record: ExerciseRecord, filename: str) -> str | None:
    canonical_path = record.canonical_dir / filename
    if canonical_path.is_file():
        return canonical_path.read_text(encoding="utf-8")

    if record.shadow_dir is None:
        return None

    shadow_path = record.shadow_dir / filename
    if shadow_path.is_file():
        return shadow_path.read_text(encoding="utf-8")
    return None


def _rewrite_exercise_doc(text: str, record: ExerciseRecord) -> str:
    updated = text
    updated = updated.replace(
        "Open the matching notebook in `notebooks/`.",
        "Open `notebooks/student.ipynb`.",
    )
    updated = updated.replace(
        "Run `pytest -q` until all tests pass.",
        f"Run `pytest -q tests/test_{record.exercise_key}.py` until all tests pass.",
    )

    replacements = (
        (
            rf"(?:\.\./)+notebooks/solutions/{re.escape(record.exercise_key)}\.ipynb",
            "notebooks/solution.ipynb",
        ),
        (
            rf"(?:\.\./)+notebooks/{re.escape(record.exercise_key)}\.ipynb",
            "notebooks/student.ipynb",
        ),
        (
            rf"notebooks/solutions/{re.escape(record.exercise_key)}\.ipynb",
            "notebooks/solution.ipynb",
        ),
        (
            rf"notebooks/{re.escape(record.exercise_key)}\.ipynb",
            "notebooks/student.ipynb",
        ),
        (
            rf"exercises/{re.escape(record.construct)}/{re.escape(record.exercise_key)}/"
            rf"tests/test_{re.escape(record.exercise_key)}\.py",
            f"tests/test_{record.exercise_key}.py",
        ),
        (
            rf"(?:\.\./)+{re.escape(record.exercise_key)}/tests/"
            rf"test_{re.escape(record.exercise_key)}\.py",
            f"tests/test_{record.exercise_key}.py",
        ),
        (
            rf"exercises/{re.escape(record.construct)}/{re.escape(record.exercise_type)}/"
            rf"{re.escape(record.exercise_key)}/",
            f"exercises/{record.construct}/{record.exercise_key}/",
        ),
    )

    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, updated)
    return updated


def _plan_doc_rewrite_actions(record: ExerciseRecord, repo_root: Path) -> list[Action]:
    actions: list[Action] = []
    for filename in DOC_FILENAMES:
        current_text = _existing_doc_text(record, filename)
        if current_text is None:
            continue

        rewritten_text = _rewrite_exercise_doc(current_text, record)
        if rewritten_text == current_text:
            continue

        destination = record.canonical_dir / filename
        actions.append(
            Action(
                kind="write_text",
                description=(
                    f"rewrite local links in {_relative_to_repo(destination, repo_root)}"),
                destination=destination,
                content=rewritten_text,
            )
        )
    return actions


def _rewrite_order_of_teaching(text: str, exercises: list[ExerciseRecord]) -> str:
    updated = text
    for record in exercises:
        updated = updated.replace(
            f"[Supporting docs](./{record.exercise_type}/{record.exercise_key}/)",
            f"[Supporting docs](./{record.exercise_key}/)",
        )
        updated = updated.replace(
            f"[Notebook](notebooks/{record.exercise_key}.ipynb)",
            f"[Notebook](./{record.exercise_key}/notebooks/student.ipynb)",
        )
    return updated


def _plan_order_of_teaching_action(
    repo_root: Path,
    *,
    construct: str,
    exercises: list[ExerciseRecord],
) -> list[Action]:
    order_path = repo_root / "exercises" / construct / "OrderOfTeaching.md"
    if not order_path.is_file():
        return []

    current_text = order_path.read_text(encoding="utf-8")
    rewritten_text = _rewrite_order_of_teaching(current_text, exercises)
    if rewritten_text == current_text:
        return []

    return [
        Action(
            kind="write_text",
            description=(
                "update canonical notebook/supporting-doc links in "
                f"{_relative_to_repo(order_path, repo_root)}"
            ),
            destination=order_path,
            content=rewritten_text,
        )
    ]


def _plan_manifest_action(repo_root: Path, exercises: list[ExerciseRecord]) -> list[Action]:
    manifest_path = repo_root / MANIFEST_PATH
    manifest = _load_json_object(manifest_path)

    exercises_obj = manifest.get("exercises")
    if not isinstance(exercises_obj, dict):
        raise MigrationError(
            f"Expected an 'exercises' object in {manifest_path}")

    changed = False
    for record in exercises:
        entry = exercises_obj.get(record.exercise_key)
        if not isinstance(entry, dict):
            exercises_obj[record.exercise_key] = {"layout": "canonical"}
            changed = True
            continue
        if entry.get("layout") != "canonical":
            entry["layout"] = "canonical"
            changed = True

    if not changed:
        return []

    manifest_text = json.dumps(manifest, indent=2) + "\n"
    return [
        Action(
            kind="write_manifest",
            description=(
                "mark migrated exercises as canonical in "
                f"{_relative_to_repo(manifest_path, repo_root)}"
            ),
            destination=manifest_path,
            content=manifest_text,
        )
    ]


def _plan_legacy_type_root_cleanup_actions(
    repo_root: Path,
    *,
    construct: str,
    exercises: list[ExerciseRecord],
) -> list[Action]:
    construct_dir = repo_root / "exercises" / construct

    actions: list[Action] = []
    for exercise_type in LEGACY_EXERCISE_TYPES:
        legacy_root = construct_dir / exercise_type
        if not legacy_root.is_dir():
            continue
        matching_shadow_dirs = {
            record.shadow_dir
            for record in exercises
            if record.shadow_dir is not None and record.exercise_type == exercise_type
        }
        if any(path not in matching_shadow_dirs for path in legacy_root.iterdir()):
            continue
        actions.append(
            Action(
                kind="cleanup_dir",
                description=(
                    f"remove empty legacy directory {_relative_to_repo(legacy_root, repo_root)}"
                ),
                source=legacy_root,
            )
        )
    return actions


def _build_actions(
    repo_root: Path,
    *,
    construct: str,
    exercises: list[ExerciseRecord],
) -> list[Action]:
    actions: list[Action] = []

    for record in exercises:
        actions.extend(_plan_notebook_actions(record, repo_root))
    for record in exercises:
        actions.extend(_plan_shadow_actions(record, repo_root))
    actions.extend(
        _plan_legacy_type_root_cleanup_actions(
            repo_root,
            construct=construct,
            exercises=exercises,
        )
    )
    for record in exercises:
        actions.extend(_plan_doc_rewrite_actions(record, repo_root))

    actions.extend(
        _plan_order_of_teaching_action(
            repo_root, construct=construct, exercises=exercises)
    )
    actions.extend(_plan_manifest_action(repo_root, exercises))
    return actions


def _collect_remaining_legacy_sources(repo_root: Path, construct: str) -> list[Path]:
    remaining: list[Path] = []

    notebook_roots = (
        repo_root / "notebooks",
        repo_root / "notebooks" / "solutions",
    )
    for notebook_root in notebook_roots:
        if not notebook_root.is_dir():
            continue
        for notebook_path in sorted(notebook_root.glob(f"*_{construct}_*.ipynb")):
            remaining.append(notebook_path)

    construct_dir = repo_root / "exercises" / construct
    for exercise_type in LEGACY_EXERCISE_TYPES:
        legacy_root = construct_dir / exercise_type
        if not legacy_root.is_dir():
            continue
        for path in sorted(legacy_root.iterdir()):
            remaining.append(path)

    return remaining


def _prune_empty_directories(root: Path) -> None:
    if not root.exists():
        return

    nested_dirs = sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for path in nested_dirs:
        if not any(path.iterdir()):
            path.rmdir()
    if root.exists() and not any(root.iterdir()):
        root.rmdir()


def _apply_move_copy(action: Action) -> None:
    if action.source is None or action.destination is None:
        raise MigrationError(f"Invalid move action: {action}")
    if action.destination.exists():
        raise MigrationConflictError(
            f"Conflict: {action.destination} already exists")
    action.destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(action.source, action.destination)


def _apply_move_cleanup(action: Action) -> None:
    if action.source is None:
        raise MigrationError(f"Invalid move action: {action}")
    action.source.unlink()


def _apply_remove(action: Action) -> None:
    if action.source is None:
        raise MigrationError(f"Invalid remove action: {action}")
    action.source.unlink()


def _apply_write(action: Action) -> None:
    if action.destination is None or action.content is None:
        raise MigrationError(f"Invalid write action: {action}")
    action.destination.parent.mkdir(parents=True, exist_ok=True)
    action.destination.write_text(action.content, encoding="utf-8")


def _apply_cleanup(action: Action) -> None:
    if action.source is None:
        raise MigrationError(f"Invalid cleanup action: {action}")
    _prune_empty_directories(action.source)


def _apply_action_stage(
    actions: list[Action],
    *,
    handlers: dict[str, Callable[[Action], None]],
    skipped_kinds: set[str],
) -> None:
    for action in actions:
        handler = handlers.get(action.kind)
        if handler is not None:
            handler(action)
            continue
        if action.kind in skipped_kinds:
            continue
        raise MigrationError(f"Unsupported action kind: {action.kind}")


def _apply_actions(actions: list[Action]) -> None:
    _apply_action_stage(
        actions,
        handlers={
            "move_file": _apply_move_copy,
            "write_text": _apply_write,
            "write_manifest": _apply_write,
        },
        skipped_kinds={"remove_file", "cleanup_dir"},
    )
    _apply_action_stage(
        actions,
        handlers={
            "move_file": _apply_move_cleanup,
            "remove_file": _apply_remove,
            "cleanup_dir": _apply_cleanup,
        },
        skipped_kinds={"write_text", "write_manifest"},
    )


def _print_report(
    repo_root: Path,
    *,
    construct: str,
    actions: list[Action],
    remaining_legacy_sources: list[Path],
    apply: bool,
) -> None:
    action_label = "Performed" if apply else "Planned"
    mode = "apply" if apply else "dry-run"

    print(f"Mode: {mode}")
    print(f"Construct: {construct}")
    print()
    print(f"{action_label} actions:")
    if not actions:
        print("- none")
    else:
        for action in actions:
            print(f"- {action.description}")

    print()
    print("Remaining legacy sources:")
    if not remaining_legacy_sources:
        print("- none")
        return

    for path in remaining_legacy_sources:
        print(f"- {_relative_to_repo(path, repo_root)}")


def main(argv: list[str] | None = None) -> int:
    """Run the one-off migration planner or apply the migration."""
    args = _parse_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        exercises = _discover_exercises(repo_root, args.construct)
        actions = _build_actions(
            repo_root, construct=args.construct, exercises=exercises)
        if args.apply:
            _apply_actions(actions)
        remaining_legacy_sources = _collect_remaining_legacy_sources(
            repo_root, args.construct)
    except (MigrationError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1

    _print_report(
        repo_root,
        construct=args.construct,
        actions=actions,
        remaining_legacy_sources=remaining_legacy_sources,
        apply=args.apply,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
