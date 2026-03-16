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
import uuid
from pathlib import Path
from typing import Any

from exercise_metadata.schema import SCHEMA_VERSION

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


def _make_meta(language: str, *, tags: list[str] | None = None) -> dict[str, Any]:
    """Create cell metadata dictionary."""
    meta: dict[str, object] = {"id": uuid.uuid4().hex[:8], "language": language}
    if tags:
        meta["tags"] = tags
    return meta


def _make_debug_cells(parts: int) -> list[dict[str, Any]]:
    """Create debug exercise cells."""
    cells: list[dict[str, Any]] = []
    for i in range(1, parts + 1):
        exercise_tag = f"exercise{i}"
        explanation_tag = f"explanation{i}"
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": _make_meta("markdown"),
                "source": [
                    f"# Exercise {i} — Expected behaviour\n",
                    "Describe what the corrected program should output.\n",
                    "### Expected output\n",
                    "```\n",
                    "(put example output here)\n",
                    "```\n",
                ],
            }
        )
        cells.append(
            {
                "cell_type": "code",
                "metadata": _make_meta("python", tags=[exercise_tag]),
                "execution_count": None,
                "outputs": [],
                "source": [
                    "# BUGGY CODE (students edit this tagged cell)\n",
                    "# Fix the code below and run the cell.\n",
                    "\n",
                    "print('TODO: Fix this code')\n",
                ],
            }
        )
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": _make_meta("markdown", tags=[explanation_tag]),
                "source": [
                    "### What actually happened\n",
                    "Describe briefly what happened when you ran the code "
                    "(include any error messages or incorrect output).\n",
                ],
            }
        )

    return cells


def _make_standard_cells(parts: int) -> list[dict[str, Any]]:
    """Create standard (non-debug) exercise cells."""
    cells: list[dict[str, Any]] = []
    if parts == 1:
        cells.append(
            {
                "cell_type": "code",
                "metadata": _make_meta("python", tags=["exercise1"]),
                "execution_count": None,
                "outputs": [],
                "source": [
                    "# Exercise 1\n",
                    "# The tests will execute the code in this cell and verify the output.\n",
                    "# Write your code below.\n",
                    "\n",
                    "print('TODO: Write your solution here')\n",
                ],
            }
        )
        return cells

    for i in range(1, parts + 1):
        exercise_tag = f"exercise{i}"
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": _make_meta("markdown"),
                "source": [
                    f"## Exercise {i}\n",
                    "(Write the prompt here.)\n",
                ],
            }
        )
        cells.append(
            {
                "cell_type": "code",
                "metadata": _make_meta("python", tags=[exercise_tag]),
                "execution_count": None,
                "outputs": [],
                "source": [
                    f"# Exercise {i}\n",
                    "# The tests will execute the code in this cell and verify the output.\n",
                    "# Write your code below.\n",
                    "\n",
                    "print('TODO: Write your solution here')\n",
                ],
            }
        )

    return cells


def _make_check_answers_cell(notebook_filename: str) -> dict[str, Any]:
    """Return the auto-generated check-your-answers cell for the notebook."""
    return {
        "cell_type": "code",
        "metadata": _make_meta("python"),
        "execution_count": None,
        "outputs": [],
        "source": [
            "from exercise_runtime_support.student_checker import run_notebook_checks\n",
            "\n",
            f"run_notebook_checks({notebook_filename!r})\n",
        ],
    }


def _make_notebook_with_parts(
    title: str,
    *,
    parts: int,
    exercise_type: str,
    notebook_filename: str,
    test_target: str,
) -> dict[str, Any]:
    """Build a scaffolded notebook with tagged exercise cells."""
    if parts < 1:
        raise ValueError("parts must be >= 1")

    cells: list[dict[str, Any]] = [
        {
            "cell_type": "markdown",
            "metadata": _make_meta("markdown"),
            "source": [
                f"# {title}\n",
                "\n",
                "## Goal\n",
                "Complete each exercise cell, then run the tests.\n",
                "\n",
                "## How to work\n",
                "- Write your solution(s) in the exercise cell(s)\n",
                f"- Run `pytest -q {test_target}`\n",
            ],
        }
    ]

    if exercise_type == "debug":
        cells.extend(_make_debug_cells(parts))
    else:
        cells.extend(_make_standard_cells(parts))

    cells.append(
        {
            "cell_type": "code",
            "metadata": _make_meta("python"),
            "execution_count": None,
            "outputs": [],
            "source": [
                "# Self-check scratch cell (not graded)\n",
                "# You can run small experiments here.\n",
            ],
        }
    )
    cells.append(_make_check_answers_cell(notebook_filename))

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _build_readme_lines(
    title: str,
    created_date: str,
    *,
    exercise_type: str,
    test_target: str,
) -> list[str]:
    """Build README content for a scaffolded exercise."""
    lines = [
        f"# {title}",
        "",
        "## Student prompt",
        "- Open `notebooks/student.ipynb`.",
        "- Write your solution in the notebook cell tagged `exercise1` (or `exercise2`, …).",
        f"- Run `pytest -q {test_target}` until all tests pass.",
        "",
        "## Teacher notes",
        f"- Created: {created_date}",
        "- Target concepts: (fill in)",
    ]
    if exercise_type == "debug":
        lines.insert(
            6,
            "- After running your corrected solution, describe what happened in the cell "
            "tagged `explanation1` (or `explanationN`).",
        )
    return lines


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
    parser = argparse.ArgumentParser(description="Create a new exercise skeleton")
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
        choices=["debug", "modify", "make"],
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
        raise SystemExit(f"--parts is capped at {MAX_PARTS} to keep notebooks manageable")

    exercise_id = args.exercise_id.strip().lower()
    if not re.fullmatch(r"ex\d{3}", exercise_id):
        raise SystemExit('Exercise id must look like "ex001".')

    construct = args.construct.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", construct):
        raise SystemExit(
            "--construct must be snake_case containing only a-z, 0-9, and underscores."
        )

    slug = args.slug.strip().lower() if args.slug else _slugify(args.title)
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", slug):
        raise SystemExit("Slug must be snake_case containing only a-z, 0-9, and underscores.")

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
    args = _validate_and_parse_args()
    exercise_key = _build_exercise_key(
        args.exercise_id,
        args.construct,
        args.exercise_type,
        args.slug,
    )

    _check_exercise_not_exists(args.construct, args.exercise_type, exercise_key)

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
    readme_lines = _build_readme_lines(
        args.title,
        today,
        exercise_type=args.exercise_type,
        test_target=test_path.relative_to(ROOT).as_posix(),
    )
    (exercise_dir / README_FILENAME).write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    exercise_metadata = _build_exercise_metadata(
        args,
        exercise_key=exercise_key,
    )
    (exercise_dir / "exercise.json").write_text(
        json.dumps(exercise_metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    relative_student_notebook = student_notebook_path.relative_to(ROOT).as_posix()
    relative_test_path = test_path.relative_to(ROOT).as_posix()
    test_lines: list[str] = [
        "from __future__ import annotations",
        "",
        "import pytest",
        "",
        "from exercise_runtime_support.exercise_framework import runtime",
        "",
        f"NOTEBOOK_PATH = {relative_student_notebook!r}",
        "",
        "",
        "def _run_and_capture(tag: str) -> str:",
        '    """Execute the tagged cell and capture its print output."""',
        "    return runtime.run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag)",
        "",
        "",
    ]

    if args.parts == 1:
        test_lines.extend(
            [
                "def test_exercise1_output() -> None:",
                "    output = _run_and_capture('exercise1')",
                "    # TODO: Add assertions to verify the output",
                "    # Placeholder guard: ensure students replace the TODO",
                "    assert output.strip(), 'Exercise should produce output'",
                "    assert 'TODO' not in output, 'Replace the TODO placeholder with your solution'",
                "    # Example: assert 'expected text' in output",
                "",
            ]
        )
    else:
        exercise_tags = ", ".join(f"'exercise{i}'" for i in range(1, args.parts + 1))
        test_lines.extend(
            [
                f"@pytest.mark.parametrize('tag', [{exercise_tags}])",
                "def test_exercise_cells_execute(tag: str) -> None:",
                '    """Verify each tagged cell executes without error."""',
                "    output = _run_and_capture(tag)",
                "    # Placeholder guard: ensure students replace the TODO",
                "    assert output.strip(), f'{tag} should produce output'",
                "    assert 'TODO' not in output, f'Replace the TODO placeholder in {tag}'",
                "",
            ]
        )

    if args.exercise_type == "debug":
        test_lines.extend(
            [
                "# Explanation cell checks for debug exercises",
                "",
            ]
        )
        if args.parts == 1:
            test_lines.extend(
                [
                    "def test_explanation_has_content() -> None:",
                    "    explanation = runtime.get_explanation_cell(NOTEBOOK_PATH, tag='explanation1')",
                    "    assert len(explanation.strip()) > 10, 'Explanation must be more than 10 characters'",
                    "",
                ]
            )
        else:
            test_lines.extend(
                [
                    f"EXPLANATION_TAGS = [f'explanation{{i}}' for i in range(1, {args.parts} + 1)]",
                    "@pytest.mark.parametrize('tag', EXPLANATION_TAGS)",
                    "def test_explanations_have_content(tag: str) -> None:",
                    "    explanation = runtime.get_explanation_cell(NOTEBOOK_PATH, tag=tag)",
                    "    assert len(explanation.strip()) > 10, 'Explanation must be more than 10 characters'",
                    "",
                ]
            )

    test_path.write_text("\n".join(test_lines), encoding="utf-8")

    notebook = _make_notebook_with_parts(
        args.title,
        parts=args.parts,
        exercise_type=args.exercise_type,
        notebook_filename=STUDENT_NOTEBOOK_FILENAME,
        test_target=relative_test_path,
    )
    student_notebook_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    solution_notebook_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")

    print(f"Created exercise: {exercise_key}")
    print(f"- {exercise_dir.relative_to(ROOT)}")
    print(f"- {(exercise_dir / 'exercise.json').relative_to(ROOT)}")
    print(f"- {student_notebook_path.relative_to(ROOT)}")
    print(f"- {solution_notebook_path.relative_to(ROOT)}")
    print(f"- {test_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
