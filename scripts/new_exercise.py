#!/usr/bin/env python3
"""Scaffold a new exercise in the canonical exercise layout.

Usage:
  python scripts/new_exercise.py ex001 "Variables and Types" \
      --construct sequence --type modify --slug variables_and_types
  python scripts/new_exercise.py ex010 "Week 1" \
      --construct sequence --type debug --slug week1 --parts 3

This creates:
  exercises/<construct>/<exercise_key>/README.md
  exercises/<construct>/<exercise_key>/exercise.json
  exercises/<construct>/<exercise_key>/notebooks/student.ipynb
  exercises/<construct>/<exercise_key>/notebooks/solution.ipynb
  exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from pathlib import Path

from exercise_metadata.schema import SCHEMA_VERSION
from scripts.template_repo_cli.utils.validation import VALID_CONSTRUCTS, validate_construct_name

ROOT = Path(__file__).resolve().parents[1]
MAX_PARTS = 20
README_FILENAME = "README.md"
STUDENT_NOTEBOOK_FILENAME = "student.ipynb"
SOLUTION_NOTEBOOK_FILENAME = "solution.ipynb"


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        raise SystemExit("Slug is empty; provide --slug or a better title.")
    return text


def _build_exercise_key(
    exercise_id: str,
    construct: str,
    exercise_type: str,
    slug: str,
) -> str:
    """Build the canonical exercise key from scaffold inputs.

    Args:
        exercise_id: Exercise identifier in ``exNNN`` format.
        construct: Canonical construct name.
        exercise_type: Canonical exercise type.
        slug: Snake-case exercise slug suffix.

    Returns:
        The exercise key in ``exNNN_<construct>_<type>_<slug>`` format.
    """
    return f"{exercise_id}_{construct}_{exercise_type}_{slug}"


def _build_exercise_metadata(
    args: argparse.Namespace,
    *,
    exercise_key: str,
) -> dict[str, int | str]:
    """Build exercise.json contents for the scaffolded exercise."""
    return {
        "schema_version": SCHEMA_VERSION,
        "exercise_key": exercise_key,
        "exercise_id": int(args.exercise_id[2:]),
        "slug": exercise_key,
        "title": args.title,
        "construct": args.construct,
        "exercise_type": args.exercise_type,
        "parts": args.parts,
    }


def _validate_and_parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a new exercise skeleton")
    parser.add_argument("exercise_id", help='Exercise id like "ex001"')
    parser.add_argument("title", help="Human title for the exercise")
    parser.add_argument(
        "--construct",
        required=True,
        help="Programming construct for the exercise, for example 'sequence'.",
    )
    parser.add_argument(
        "--type",
        dest="exercise_type",
        required=True,
        choices=["debug", "modify", "make", "gaps"],
        help="Exercise type for the scaffold.",
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="Optional slug suffix (snake_case). Defaults to a slugified title.",
    )
    parser.add_argument(
        "--parts",
        type=int,
        default=1,
        help="How many graded exercise cells to scaffold in the notebook (default: 1).",
    )
    args = parser.parse_args()

    if args.parts < 1:
        raise SystemExit("--parts must be >= 1")
    if args.parts > MAX_PARTS:
        raise SystemExit(
            f"--parts is capped at {MAX_PARTS} to keep notebooks manageable")

    exercise_id = args.exercise_id.strip().lower()
    if not re.fullmatch(r"ex\d{3}", exercise_id):
        raise SystemExit('Exercise id must look like "ex001".')

    construct = args.construct.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", construct):
        raise SystemExit(
            "--construct must be snake_case containing only a-z, 0-9, and underscores."
        )
    if not validate_construct_name(construct):
        valid_constructs = ", ".join(sorted(VALID_CONSTRUCTS))
        raise SystemExit(
            f"Unknown construct: {construct}. Use one of: {valid_constructs}.")

    slug = args.slug.strip().lower() if args.slug else _slugify(args.title)
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", slug):
        raise SystemExit(
            "Slug must be snake_case containing only a-z, 0-9, and underscores.")

    args.exercise_id = exercise_id
    args.construct = construct
    args.slug = slug
    return args


def _check_exercise_not_exists(
    construct: str,
    exercise_type: str,
    exercise_key: str,
) -> None:
    """Raise SystemExit if the exercise already exists in supported layouts."""
    paths_to_check = [
        ROOT / "exercises" / construct / exercise_key,
        ROOT / "exercises" / construct / exercise_type / exercise_key,
        ROOT / "exercises" / exercise_key,
        ROOT / "notebooks" / f"{exercise_key}.ipynb",
        ROOT / "notebooks" / "solutions" / f"{exercise_key}.ipynb",
        ROOT / "tests" / f"test_{exercise_key}.py",
    ]
    if any(path.exists() for path in paths_to_check):
        raise SystemExit(f"Exercise already exists: {exercise_key}")


def main() -> int:
    """Create a new canonical exercise scaffold."""
    from scripts.exercise_scaffolder import (
        DebugScaffold,
        GapsScaffold,
        MakeScaffold,
        ModifyScaffold,
    )

    args = _validate_and_parse_args()
    exercise_key = _build_exercise_key(
        args.exercise_id,
        args.construct,
        args.exercise_type,
        args.slug,
    )

    _check_exercise_not_exists(
        args.construct, args.exercise_type, exercise_key)

    exercise_dir = ROOT / "exercises" / args.construct / exercise_key
    notebooks_dir = exercise_dir / "notebooks"
    tests_dir = exercise_dir / "tests"
    student_notebook_path = notebooks_dir / STUDENT_NOTEBOOK_FILENAME
    solution_notebook_path = notebooks_dir / SOLUTION_NOTEBOOK_FILENAME
    test_path = tests_dir / f"test_{exercise_key}.py"

    exercise_dir.mkdir(parents=True)
    notebooks_dir.mkdir()
    tests_dir.mkdir()
    (exercise_dir / "__init__.py").write_text("\n", encoding="utf-8")

    today = _dt.date.today().isoformat()
    relative_test_path = test_path.relative_to(ROOT).as_posix()

    # Instantiate the type-specific scaffold
    scaffold_class = {
        "debug": DebugScaffold,
        "modify": ModifyScaffold,
        "make": MakeScaffold,
        "gaps": GapsScaffold,
    }[args.exercise_type]
    scaffold = scaffold_class(
        title=args.title,
        exercise_key=exercise_key,
        parts=args.parts,
        test_target=relative_test_path,
        exercise_id=int(args.exercise_id[2:]),
    )

    # README
    readme_lines = scaffold.build_readme_lines(today)
    (exercise_dir / README_FILENAME).write_text(
        "\n".join(readme_lines) + "\n", encoding="utf-8"
    )

    # exercise.json
    exercise_metadata = _build_exercise_metadata(
        args,
        exercise_key=exercise_key,
    )
    (exercise_dir / "exercise.json").write_text(
        json.dumps(exercise_metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    # Test file
    test_lines = scaffold.build_test_lines()
    test_path.write_text("\n".join(test_lines), encoding="utf-8")

    # Notebooks (student and solution variants)
    student_notebook = scaffold.build_notebook(
        "student", exercise_type=args.exercise_type
    )
    solution_notebook = scaffold.build_notebook(
        "solution", exercise_type=args.exercise_type
    )
    student_notebook_path.write_text(
        json.dumps(student_notebook, indent=2), encoding="utf-8"
    )
    solution_notebook_path.write_text(
        json.dumps(solution_notebook, indent=2), encoding="utf-8"
    )

    # Supporting files
    expectations_module = scaffold.build_expectations_module()
    (tests_dir / "expectations.py").write_text(
        expectations_module, encoding="utf-8"
    )

    checker_support = scaffold.build_student_checker_support()
    (tests_dir / "student_checker_support.py").write_text(
        checker_support, encoding="utf-8"
    )

    print(f"Created exercise: {exercise_key}")
    print(f"- {exercise_dir.relative_to(ROOT)}")
    print(f"- {(exercise_dir / 'exercise.json').relative_to(ROOT)}")
    print(f"- {student_notebook_path.relative_to(ROOT)}")
    print(f"- {solution_notebook_path.relative_to(ROOT)}")
    print(f"- {test_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
