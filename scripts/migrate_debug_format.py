"""Migrate old debug exercise notebooks to the new 5-cell format.

Old format (3 cells per exercise):
  1. Markdown description
  2. Code cell with tag exerciseN (buggy code)
  3. Markdown explanation with tag explanationN

New format (5 cells per exercise):
  1. Markdown description
  2. Read-only code cell (no exercise tag, deletable:false, editable:false)
  3. Markdown explanation with tag explanationN
  4. Markdown header "### 🐞 Debug this code"
  5. Code cell with tag exerciseN (editable buggy code)
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


def _make_readonly_meta(exercise_tag: str) -> dict[str, Any]:
    """Create metadata for a read-only buggy code cell."""
    return {
        "id": exercise_tag.replace("exercise", "readonly") + "_meta",
        "language": "python",
        "deletable": False,
        "editable": False,
    }


def _make_debug_header_cell() -> dict[str, Any]:
    """Create the '### 🐞 Debug this code' markdown header cell."""
    return {
        "cell_type": "markdown",
        "metadata": {
            "id": "debug_header",
            "language": "markdown",
        },
        "source": ["### \U0001f41e Debug this code\n"],
    }


def _make_finished_prompt_cell() -> dict[str, Any]:
    """Create the 'Finished? Check your work' prompt cell."""
    return {
        "cell_type": "markdown",
        "metadata": {
            "id": "finished_prompt",
            "language": "markdown",
        },
        "source": ["\U0001f3c1\uFE0F **Finished?** \u2705 [Check your work](#check-your-work).\n"],
    }


def _make_self_check_scratch_cell() -> dict[str, Any]:
    """Create the self-check scratch cell at the end of the notebook."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {
            "id": "self_check_scratch",
            "language": "python",
            "tags": [],
        },
        "outputs": [],
        "source": [
            "# Self-check scratch cell (not graded)\n",
            "# You can run small experiments here.\n",
        ],
    }


def _make_check_your_work_header_cell() -> dict[str, Any]:
    """Create the 'Check your work' header cell."""
    return {
        "cell_type": "markdown",
        "metadata": {
            "id": "check_your_work_header",
            "language": "markdown",
        },
        "source": [
            "## Check your work\n",
            "Run the code below to find out if you have completed your tasks correctly\n",
        ],
    }


def _make_check_answers_cell(exercise_key: str, variant: str) -> dict[str, Any]:
    """Create the check answers cell with run_notebook_checks.

    For solution variants, includes PYTUTOR_ACTIVE_VARIANT env var setup.
    """
    source_lines: list[str] = []
    if variant == "solution":
        source_lines.extend([
            "import os\n",
            "\n",
            'os.environ["PYTUTOR_ACTIVE_VARIANT"] = "solution"\n',
            "\n",
        ])
    source_lines.extend([
        "from exercise_runtime_support.student_checker import run_notebook_checks\n",
        "\n",
        f"run_notebook_checks('{exercise_key}')\n",
    ])
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {
            "id": "check_answers",
            "language": "python",
            "tags": [],
        },
        "outputs": [],
        "source": source_lines,
    }


def _get_tags(cell: dict[str, Any]) -> list[str]:
    """Extract tags from a cell's metadata."""
    tags = cell.get("metadata", {}).get("tags", [])
    return tags if isinstance(tags, list) else []


def _has_tag(cell: dict[str, Any], pattern: str) -> bool:
    """Check if a cell has a tag matching the given regex pattern."""
    return any(re.match(pattern, t) for t in _get_tags(cell))


def _is_exercise_code(cell: dict[str, Any]) -> bool:
    """Check if a cell is an exercise code cell."""
    return cell.get("cell_type") == "code" and _has_tag(cell, r"^exercise\d+$")


def _is_explanation(cell: dict[str, Any]) -> bool:
    """Check if a cell is an explanation markdown cell."""
    return cell.get("cell_type") == "markdown" and _has_tag(cell, r"^explanation\d+$")


def _is_description(cell: dict[str, Any]) -> bool:
    """Check if a cell is a description markdown (no exercise/explanation tags)."""
    if cell.get("cell_type") != "markdown":
        return False
    return not _has_tag(cell, r"^exercise\d+$") and not _has_tag(cell, r"^explanation\d+$")


def _find_description_before(cells: list[dict[str, Any]], code_idx: int, consumed: set[int]) -> int | None:
    """Find the description markdown cell before a code cell."""
    idx = code_idx - 1
    while idx >= 0:
        if idx in consumed:
            idx -= 1
            continue
        cell = cells[idx]
        if cell.get("cell_type") != "markdown":
            break
        if _is_description(cell):
            return idx
        break
        idx -= 1
    return None


def _find_explanation_after(cells: list[dict[str, Any]], code_idx: int, consumed: set[int]) -> int | None:
    """Find the explanation markdown cell after a code cell."""
    idx = code_idx + 1
    while idx < len(cells):
        if idx in consumed:
            idx += 1
            continue
        cell = cells[idx]
        if cell.get("cell_type") == "markdown":
            if _is_explanation(cell):
                return idx
            break
        break
        idx += 1
    return None


def _build_exercise_indices(cells: list[dict[str, Any]]) -> dict[int, int]:
    """Map exercise number to cell index for all exercise code cells."""
    indices: dict[int, int] = {}
    for i, cell in enumerate(cells):
        if _is_exercise_code(cell):
            for tag in _get_tags(cell):
                m = re.match(r"^exercise(\d+)$", tag)
                if m:
                    indices[int(m.group(1))] = i
                    break
    return indices


def _build_single_exercise_group(
    cells: list[dict[str, Any]],
    exercise_no: int,
    code_idx: int,
    consumed: set[int],
) -> dict[str, Any]:
    """Build one exercise group with its description and explanation."""
    group_cells: list[dict[str, Any]] = []

    desc_idx = _find_description_before(cells, code_idx, consumed)
    if desc_idx is not None:
        group_cells.append(cells[desc_idx])
        consumed.add(desc_idx)

    group_cells.append(cells[code_idx])
    consumed.add(code_idx)

    expl_idx = _find_explanation_after(cells, code_idx, consumed)
    if expl_idx is not None:
        group_cells.append(cells[expl_idx])
        consumed.add(expl_idx)

    return {
        "type": "exercise",
        "cells": group_cells,
        "exercise_no": exercise_no,
    }


def _build_final_groups(
    cells: list[dict[str, Any]],
    exercise_groups: list[dict[str, Any]],
    consumed: set[int],
) -> list[dict[str, Any]]:
    """Build the final groups list preserving original cell order."""
    groups: list[dict[str, Any]] = []
    for i, cell in enumerate(cells):
        if i in consumed:
            for eg in exercise_groups:
                if cell in eg["cells"] and eg not in groups:
                    groups.append(eg)
                    break
        else:
            groups.append({"type": "section", "cells": [cell]})
    return groups


def _extract_exercise_groups(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse cells into a list of groups: section headers and exercise groups.

    Returns a list of dicts with keys:
      - 'type': 'section' or 'exercise'
      - 'cells': list of cells in the group
      - 'exercise_no': (exercise only) the exercise number

    Each exercise group contains: description markdown + code cell + explanation markdown.
    Section groups contain any non-exercise cells.
    """
    exercise_indices = _build_exercise_indices(cells)
    exercise_groups: list[dict[str, Any]] = []
    consumed: set[int] = set()

    for exercise_no in sorted(exercise_indices.keys()):
        group = _build_single_exercise_group(
            cells, exercise_no, exercise_indices[exercise_no], consumed
        )
        exercise_groups.append(group)

    return _build_final_groups(cells, exercise_groups, consumed)


def _find_code_cell(cells: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the exercise code cell in a list of cells."""
    for cell in cells:
        if _is_exercise_code(cell):
            return cell
    return None


def _find_description_cell(cells: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the description markdown cell in a list of cells."""
    for cell in cells:
        if _is_description(cell):
            return cell
    return None


def _find_explanation_cell(cells: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the explanation markdown cell in a list of cells."""
    for cell in cells:
        if _is_explanation(cell):
            return cell
    return None


def _migrate_exercise_group(
    group: dict[str, Any],
    *,
    buggy_codes: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """Convert a 3-cell exercise group to the new 5-cell format.

    If buggy_codes is provided (for solution notebooks), use the buggy code
    from the student notebook for the read-only cell.
    """
    old_cells = group["cells"]
    exercise_no = group["exercise_no"]

    code_cell = _find_code_cell(old_cells)
    if code_cell is None:
        return old_cells

    # For solution notebooks, use the buggy code from student notebook
    if buggy_codes and exercise_no in buggy_codes:
        buggy_source = buggy_codes[exercise_no].splitlines(keepends=True)
    else:
        buggy_source = code_cell["source"]

    # Build the new 5-cell sequence
    new_cells: list[dict[str, Any]] = []

    # 1. Description markdown (keep as-is)
    desc_cell = _find_description_cell(old_cells)
    if desc_cell is not None:
        new_cells.append(desc_cell)

    # 2. Read-only buggy code cell (new)
    readonly_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": _make_readonly_meta(f"exercise{exercise_no}"),
        "outputs": [],
        "source": [
            "# READ-ONLY \u2014 observe the buggy code below\n",
            "# This cell is not tested. Run it to see what happens.\n",
            "\n",
            *buggy_source,
        ],
    }
    new_cells.append(readonly_cell)

    # 3. Explanation markdown (keep as-is)
    expl_cell = _find_explanation_cell(old_cells)
    if expl_cell is not None:
        new_cells.append(expl_cell)

    # 4. "Debug this code" header (new)
    new_cells.append(_make_debug_header_cell())

    # 5. Editable buggy code cell (updated metadata, keeps original source)
    editable_cell = copy.deepcopy(code_cell)
    editable_cell["metadata"] = {
        "id": code_cell.get("metadata", {}).get("id", f"ex{exercise_no:03d}"),
        "language": "python",
        "tags": [f"exercise{exercise_no}"],
    }
    new_cells.append(editable_cell)

    # 6. "Finished?" prompt (new)
    new_cells.append(_make_finished_prompt_cell())

    return new_cells


def _load_buggy_codes(student_notebook_path: Path) -> dict[int, str]:
    """Load buggy code from a student notebook keyed by exercise number."""
    with open(student_notebook_path) as f:
        nb = json.load(f)

    buggy_codes: dict[int, str] = {}
    for cell in nb.get("cells", []):
        if _is_exercise_code(cell):
            for tag in _get_tags(cell):
                m = re.match(r"^exercise(\d+)$", tag)
                if m:
                    exercise_no = int(m.group(1))
                    buggy_codes[exercise_no] = "".join(cell["source"])
                    break
    return buggy_codes


def _extract_exercise_key(notebook_path: Path) -> str:
    """Extract exercise key from the notebook path.

    Expects path like .../exercises/<construct>/<exercise_key>/notebooks/student.ipynb
    """
    parts = notebook_path.parts
    # Find 'notebooks' directory and take the parent as exercise_key
    for i, part in enumerate(parts):
        if part == "notebooks" and i > 0:
            return parts[i - 1]
    # Fallback: use filename without extension
    return notebook_path.stem


def _determine_variant(notebook_path: Path) -> str:
    """Determine if this is a student or solution notebook."""
    if "solution" in notebook_path.name:
        return "solution"
    return "student"


def _is_footer_cell(cell: dict[str, Any]) -> bool:
    """Check if a cell is a footer cell that should be replaced."""
    cell_id = cell.get("metadata", {}).get("id", "")
    # Check for known footer cell IDs
    if cell_id in ("self_check_scratch", "check_your_work_header", "check_answers"):
        return True
    # Check for truncated check answers cells (partial imports)
    if cell.get("cell_type") == "code":
        source = "".join(cell.get("source", []))
        if "run_notebook_checks" in source or "student_checker" in source:
            return True
    # Check for self-check scratch cells by content
    if cell.get("cell_type") == "code":
        source = "".join(cell.get("source", []))
        if "Self-check scratch cell" in source:
            return True
    return False


def _add_footer_cells(
    new_cells: list[dict[str, Any]],
    exercise_key: str,
    variant: str,
) -> None:
    """Add footer cells (self-check scratch, check header, check answers) to the notebook."""
    new_cells.append(_make_self_check_scratch_cell())
    new_cells.append(_make_check_your_work_header_cell())
    new_cells.append(_make_check_answers_cell(exercise_key, variant))


def migrate_notebook(
    notebook_path: Path,
    *,
    dry_run: bool = False,
    student_notebook_path: Path | None = None,
) -> dict[str, Any]:
    """Migrate a debug exercise notebook to the new 5-cell format.

    For solution notebooks, pass student_notebook_path to use buggy code
    in the read-only cells.

    Returns a summary dict with counts of exercises migrated.
    """
    with open(notebook_path) as f:
        nb = json.load(f)

    cells = nb.get("cells", [])

    # Load buggy codes if migrating a solution notebook
    buggy_codes: dict[int, str] = {}
    if student_notebook_path and student_notebook_path.exists():
        buggy_codes = _load_buggy_codes(student_notebook_path)

    # Remove any existing footer cells before processing
    cells = [cell for cell in cells if not _is_footer_cell(cell)]

    # Parse into groups
    groups = _extract_exercise_groups(cells)

    # Migrate exercise groups
    new_cells: list[dict[str, Any]] = []
    exercises_migrated = 0

    for group in groups:
        if group["type"] == "exercise":
            migrated = _migrate_exercise_group(group, buggy_codes=buggy_codes)
            new_cells.extend(migrated)
            exercises_migrated += 1
        else:
            new_cells.extend(group["cells"])

    # Add footer cells (self-check scratch, check header, check answers)
    exercise_key = _extract_exercise_key(notebook_path)
    variant = _determine_variant(notebook_path)
    _add_footer_cells(new_cells, exercise_key, variant)

    if not dry_run:
        nb["cells"] = new_cells
        with open(notebook_path, "w") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write("\n")

    return {
        "path": str(notebook_path),
        "exercises_migrated": exercises_migrated,
        "total_cells_before": len(cells),
        "total_cells_after": len(new_cells),
    }


def find_debug_exercises(repo_root: Path) -> list[Path]:
    """Find all debug exercise student notebooks in the repo."""
    exercises_dir = repo_root / "exercises"
    notebooks = []
    for exercise_json in exercises_dir.rglob("exercise.json"):
        with open(exercise_json) as f:
            data = json.load(f)
        if data.get("exercise_type") == "debug":
            notebook = exercise_json.parent / "notebooks" / "student.ipynb"
            if notebook.exists():
                notebooks.append(notebook)
    return sorted(notebooks)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate debug exercise notebooks to the new 5-cell format.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific notebook paths to migrate. If omitted, finds all debug exercises.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing files.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root directory.",
    )
    parser.add_argument(
        "--student-notebook",
        type=Path,
        default=None,
        help="Path to student notebook (for solution notebook migration).",
    )
    args = parser.parse_args()

    if args.paths:
        notebooks = [Path(p) for p in args.paths]
    else:
        notebooks = find_debug_exercises(args.repo_root)

    if not notebooks:
        print("No debug exercise notebooks found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(notebooks)} debug exercise notebook(s) to migrate.\n")

    for nb_path in notebooks:
        result = migrate_notebook(
            nb_path,
            dry_run=args.dry_run,
            student_notebook_path=args.student_notebook,
        )
        action = "Would migrate" if args.dry_run else "Migrated"
        print(
            f"  {action}: {result['path']}\n"
            f"    Exercises: {result['exercises_migrated']}\n"
            f"    Cells: {result['total_cells_before']} -> {result['total_cells_after']}\n"
        )

    if args.dry_run:
        print("Dry run complete. No files were modified.")
    else:
        print("Migration complete.")


if __name__ == "__main__":
    main()
