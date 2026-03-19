from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

EXERCISES_DIR = Path("exercises")
MIN_EXPLANATION_LENGTH = 10


def _get_canonical_student_notebooks() -> list[Path]:
    """Return canonical repository student notebooks under exercise-local homes."""
    return sorted(EXERCISES_DIR.glob("*/*/notebooks/student.ipynb"))


def _find_explanation_cells(nb_path: Path) -> Iterator[tuple[str, str]]:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        for tag in tags:
            if re.fullmatch(r"explanation\d+", tag):
                yield tag, "".join(cell.get("source", []))


def test_debug_explanations_have_content() -> None:
    """Ensure any `explanationN` cells are meaningfully filled in.

    This scans canonical student notebooks under
    `exercises/<construct>/<exercise_key>/notebooks/student.ipynb` and asserts
    that any cell tagged `explanationN` contains more than 10 non-whitespace
    characters. This enforces the instructor requirement that students provide a
    short explanation of what happened when they ran the buggy program.
    """
    for nb_path in _get_canonical_student_notebooks():
        for tag, source in _find_explanation_cells(nb_path):
            assert len(source.strip()) > MIN_EXPLANATION_LENGTH, (
                f"{nb_path} {tag} must be more than {MIN_EXPLANATION_LENGTH} characters"
            )


def test_debug_explanations_scan_targets_canonical_student_notebooks_only() -> None:
    """Ensure the explanation scan targets canonical student notebooks only."""
    scanned_notebooks = _get_canonical_student_notebooks()
    expected_notebooks = sorted(
        exercise_dir / "notebooks" / "student.ipynb"
        for exercise_dir in EXERCISES_DIR.glob("*/*")
        if (exercise_dir / "notebooks" / "student.ipynb").exists()
    )

    assert scanned_notebooks == expected_notebooks
    assert scanned_notebooks
    assert all(nb_path.is_relative_to(EXERCISES_DIR) for nb_path in scanned_notebooks)
    assert all(nb_path.name == "student.ipynb" for nb_path in scanned_notebooks)
