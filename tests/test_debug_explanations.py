from __future__ import annotations

import json
import re
from pathlib import Path

NOTEBOOK_DIR = Path("notebooks")
MIN_EXPLANATION_LENGTH = 10


def _find_explanation_cells(nb_path: Path):
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags", [])
        for tag in tags:
            if re.fullmatch(r"explanation\d+", tag):
                yield tag, "".join(cell.get("source", []))


def test_debug_explanations_have_content() -> None:
    """Ensure any `explanationN` cells are meaningfully filled in.

    This scans notebooks in `notebooks/` (excluding `notebooks/solutions/`) and
    asserts that any cell tagged `explanationN` contains more than 10
    non-whitespace characters. This enforces the instructor requirement that
    students provide a short explanation of what happened when they ran the
    buggy program.
    """
    for nb_path in NOTEBOOK_DIR.glob("*.ipynb"):
        # Skip solution mirrors
        if nb_path.parent.name == "solutions":
            continue
        for tag, source in _find_explanation_cells(nb_path):
            assert len(source.strip()) > MIN_EXPLANATION_LENGTH, (
                f"{nb_path} {tag} must be more than {MIN_EXPLANATION_LENGTH} characters"
            )
