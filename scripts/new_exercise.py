#!/usr/bin/env python3
"""Scaffold a new exercise (notebook + tests).

Usage:
  python scripts/new_exercise.py ex001 "Variables and Types" --slug variables_and_types
    python scripts/new_exercise.py ex010 "Week 1" --slug week1 --parts 3

This creates:
  exercises/ex001_variables_and_types/README.md
  notebooks/ex001_variables_and_types.ipynb
    tests/test_ex001_variables_and_types.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_PARTS = 20
README_FILENAME = "README.md"


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
    """Create debug exercise cells (expected output, buggy code, explanation)."""
    cells: list[dict[str, Any]] = []
    for i in range(1, parts + 1):
        ex_tag = f"exercise{i}"
        expl_tag = f"explanation{i}"

        # Expected behaviour / expected output cell
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

        # Buggy implementation (tagged for students to edit)
        cells.append(
            {
                "cell_type": "code",
                "metadata": _make_meta("python", tags=[ex_tag]),
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

        # What actually happened — explanation cell (tagged)
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": _make_meta("markdown", tags=[expl_tag]),
                "source": [
                    "### What actually happened\n",
                    "Describe briefly what happened when you ran the code (include any error messages or incorrect output).\n",
                ],
            }
        )

    return cells


def _make_standard_cells(parts: int) -> list[dict[str, Any]]:
    """Create standard (non-debug) exercise cells."""
    cells: list[dict[str, Any]] = []
    if parts == 1:
        tag = "exercise1"
        cells.append(
            {
                "cell_type": "code",
                "metadata": _make_meta("python", tags=[tag]),
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
    else:
        for i in range(1, parts + 1):
            tag = f"exercise{i}"
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
                    "metadata": _make_meta("python", tags=[tag]),
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


def _make_check_answers_cell(notebook_path: str) -> dict[str, Any]:
    """Return the auto-generated check-your-answers cell for the notebook."""
    return {
        "cell_type": "code",
        "metadata": _make_meta("python"),
        "execution_count": None,
        "outputs": [],
        "source": [
            "from tests.student_checker import run_notebook_checks\n",
            "\n",
            f"run_notebook_checks({notebook_path!r})\n",
        ],
    }


def _make_notebook_with_parts(
    title: str,
    *,
    parts: int,
    exercise_type: str | None = None,
    notebook_path: str | None = None,
) -> dict[str, Any]:
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
                "- Run `pytest -q`\n",
            ],
        }
    ]

    # Add exercise cells based on type
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
                "# Optional self-check (not graded)\n",
                "# You can run small experiments here.\n",
            ],
        }
    )

    if notebook_path:
        cells.append(_make_check_answers_cell(notebook_path))

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


def _build_readme_lines(title: str, created_date: str) -> list[str]:
    return [
        f"# {title}",
        "",
        "## Student prompt",
        "- Open the matching notebook in `notebooks/`.",
        "- Write your solution in the notebook cell tagged `exercise1` (or `exercise2`, …).",
        "- Run `pytest -q` until all tests pass.",
        "",
        "## Teacher notes",
        f"- Created: {created_date}",
        "- Target concepts: (fill in)",
    ]


def _validate_and_parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(description="Create a new exercise skeleton")
    parser.add_argument("id", help='Exercise id like "ex001"')
    parser.add_argument("title", help="Human title for the exercise")
    parser.add_argument(
        "--slug",
        help="Optional slug (snake_case). Defaults to slugified title.",
        default=None,
    )
    parser.add_argument(
        "--parts",
        type=int,
        default=1,
        help="How many graded exercise cells to scaffold in the notebook (default: 1).",
    )
    parser.add_argument(
        "--type",
        choices=["debug", "modify", "make"],
        default=None,
        help="Optional exercise type; when set to 'debug' the scaffold includes expected-output and explanation cells.",
    )
    args = parser.parse_args()

    if args.parts < 1:
        raise SystemExit("--parts must be >= 1")
    if args.parts > MAX_PARTS:
        raise SystemExit(
            f"--parts is capped at {MAX_PARTS} to keep notebooks manageable"
        )

    ex_id = args.id.strip().lower()
    if not re.fullmatch(r"ex\d{3}", ex_id):
        raise SystemExit('Exercise id must look like "ex001".')

    slug = args.slug.strip().lower() if args.slug else _slugify(args.title)
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", slug):
        raise SystemExit(
            "Slug must be snake_case containing only a-z, 0-9, and underscores."
        )

    return args


def _check_exercise_not_exists(exercise_key: str) -> None:
    """Raise SystemExit if exercise already exists."""
    ex_dir = ROOT / "exercises" / exercise_key
    nb_path = ROOT / "notebooks" / f"{exercise_key}.ipynb"
    nb_solution_path = ROOT / "notebooks" / "solutions" / f"{exercise_key}.ipynb"
    test_path = ROOT / "tests" / f"test_{exercise_key}.py"

    if (
        ex_dir.exists()
        or nb_path.exists()
        or nb_solution_path.exists()
        or test_path.exists()
    ):
        raise SystemExit(f"Exercise already exists: {exercise_key}")


def main() -> int:
    args = _validate_and_parse_args()

    slug = args.slug.strip().lower() if args.slug else _slugify(args.title)
    exercise_key = f"{args.id.strip().lower()}_{slug}"

    _check_exercise_not_exists(exercise_key)

    ex_dir = ROOT / "exercises" / exercise_key
    nb_path = ROOT / "notebooks" / f"{exercise_key}.ipynb"
    nb_solution_path = ROOT / "notebooks" / "solutions" / f"{exercise_key}.ipynb"
    test_path = ROOT / "tests" / f"test_{exercise_key}.py"

    ex_dir.mkdir(parents=True)
    (ex_dir / "__init__.py").write_text("\n", encoding="utf-8")

    today = _dt.date.today().isoformat()

    readme_lines = _build_readme_lines(args.title, today)
    (ex_dir / README_FILENAME).write_text(
        "\n".join(readme_lines) + "\n",
        encoding="utf-8",
    )

    test_lines: list[str] = [
        "from __future__ import annotations",
        "",
        "import pytest",
        "",
        "from tests.notebook_grader import run_cell_and_capture_output",
        "",
        f"NOTEBOOK_PATH = 'notebooks/{exercise_key}.ipynb'",
        "",
        "",
        "def _run_and_capture(tag: str) -> str:",
        '    """Execute the tagged cell and capture its print output."""',
        "    return run_cell_and_capture_output(NOTEBOOK_PATH, tag=tag)",
        "",
        "",
    ]

    if args.parts == 1:
        test_lines += [
            "def test_exercise1_output() -> None:",
            "    output = _run_and_capture('exercise1')",
            "    # TODO: Add assertions to verify the output",
            "    # Placeholder guard: ensure students replace the TODO",
            "    assert output.strip(), 'Exercise should produce output'",
            "    assert 'TODO' not in output, 'Replace the TODO placeholder with your solution'",
            "    # Example: assert 'expected text' in output",
            "",
        ]
    else:
        tags = ", ".join([f"'exercise{i}'" for i in range(1, args.parts + 1)])
        test_lines += [
            f"@pytest.mark.parametrize('tag', [{tags}])",
            "def test_exercise_cells_execute(tag: str) -> None:",
            '    """Verify each tagged cell executes without error."""',
            "    output = _run_and_capture(tag)",
            "    # Placeholder guard: ensure students replace the TODO",
            "    assert output.strip(), f'{tag} should produce output'",
            "    assert 'TODO' not in output, f'Replace the TODO placeholder in {tag}'",
            "",
        ]

    # If this is a debug exercise, add tests that assert students filled the
    # `explanationN` markdown cells with meaningful content (>10 characters).
    if args.type == "debug":
        test_lines += [
            "# Explanation cell checks for debug exercises",
            "from tests.notebook_grader import get_explanation_cell",
            "",
        ]
        if args.parts == 1:
            test_lines += [
                "def test_explanation_has_content() -> None:",
                "    explanation = get_explanation_cell(NOTEBOOK_PATH, tag='explanation1')",
                "    assert len(explanation.strip()) > 10, 'Explanation must be more than 10 characters'",
                "",
            ]
        else:
            test_lines += [
                f"EXPLANATION_TAGS = [f'explanation{{i}}' for i in range(1, {args.parts} + 1)]",
                "@pytest.mark.parametrize('tag', EXPLANATION_TAGS)",
                "def test_explanations_have_content(tag: str) -> None:",
                "    explanation = get_explanation_cell(NOTEBOOK_PATH, tag=tag)",
                "    assert len(explanation.strip()) > 10, 'Explanation must be more than 10 characters'",
                "",
            ]

    test_path.write_text("\n".join(test_lines), encoding="utf-8")

    # Build notebook with the optional exercise type (e.g., debug)
    relative_nb_path = f"notebooks/{exercise_key}.ipynb"
    notebook = _make_notebook_with_parts(
        args.title,
        parts=args.parts,
        exercise_type=args.type,
        notebook_path=relative_nb_path,
    )
    nb_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")

    nb_solution_path.parent.mkdir(parents=True, exist_ok=True)
    nb_solution_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")

    # If this is a debug exercise, update README to mention explanation tags
    if args.type == "debug":
        readme_lines = (
            (ex_dir / README_FILENAME).read_text(encoding="utf-8").splitlines()
        )
        # Add short instruction about the explanation cell
        readme_lines.insert(
            7,
            "- After running your corrected solution, describe what happened in the cell tagged `explanation1` (or `explanationN`).",
        )
        (ex_dir / README_FILENAME).write_text(
            "\n".join(readme_lines) + "\n", encoding="utf-8"
        )

    print(f"Created exercise: {exercise_key}")
    print(f"- {ex_dir.relative_to(ROOT)}")
    print(f"- {nb_path.relative_to(ROOT)}")
    print(f"- {nb_solution_path.relative_to(ROOT)}")
    print(f"- {test_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
