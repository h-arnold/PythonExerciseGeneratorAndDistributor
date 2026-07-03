# Plan: Update exercise scaffolder header and checker prompt

## Summary

Update the exercise scaffolder to replace the pytest instruction with a
self-checker link, add a visible prompt above the checker cell, and remove
the pytest line from the README.

## File affected

- `scripts/exercise_scaffolder/base.py` (all changes in this file)

## Changes

### 1. `_build_header_cells` (lines 82-123)

- Rename `## How to work` to `## Instructions`
- Remove the `## Goal` section entirely (redundant with instructions)
- Replace the pytest command bullet in all three exercise-type branches
  (gaps, debug, default) with:
  ```
  - Check whether you got it right by [running the self checker](#check-your-work) below. 👇
  ```
- Remove `test_target` from the method signature (no longer needed here)

### 2. New method `_build_check_heading_cell` (insert near line 131)

```python
def _build_check_heading_cell(self) -> dict[str, Any]:
    """Return the 'Check your work' heading cell above the self-checker."""
    return {
        "cell_type": "markdown",
        "metadata": make_meta("markdown"),
        "source": [
            "## Check your work\n",
            "\n",
            "\uFE0F **Think you're finished?** "
            "[Check your work with the self checker now](#check-your-work). \uFE0F\n",
        ],
    }
```

This provides:
- The `#check-your-work` anchor target for the header link
- A clear visual prompt right above the checker cell

### 3. `build_notebook` (lines 59-64)

Update call to `_build_header_cells` (drop `test_target` arg) and insert
the new heading cell between scratch and checker:

```python
cells.extend(self._build_header_cells(exercise_type))
cells.extend(self._build_exercise_cells())
cells.append(self._build_scratch_cell())
cells.append(self._build_check_heading_cell())       # NEW
cells.append(self.build_check_answers_cell(variant))
```

### 4. `build_readme_lines` (lines 183-207)

Remove the pytest bullet (lines 192-193):

```
- From the repository root, run ``uv run pytest -q {self.test_target}``
  until all tests pass.
```

Resulting Student prompt section:
```
## Student prompt
- Open ``notebooks/student.ipynb`` in this exercise folder.
- Write your solution in the notebook cell tagged ``exercise1``
  (or ``exercise2``, …).
```

## Resulting notebook structure

```
Header cell:   # Title → ## Instructions → link to #check-your-work
Exercise cells (×N)
Scratch cell:  # Self-check scratch cell (not graded)
## Check your work                          ← new anchor cell
🏁 Think you're finished? Check your work...  ← new prompt
Checker cell:  run_notebook_checks(...)
```

## Scope

- Only affects **newly scaffolded** exercises (existing notebooks unchanged)
- `self.test_target` remains on the class (still used by README line 192
  area if any subclass references it, though the pytest line is removed)
