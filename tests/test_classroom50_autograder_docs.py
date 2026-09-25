"""Documentation-contract tests for the generic Classroom 50 scoring contract.

The contract document is now part of the Stage 3 deliverable. These tests keep
its required content aligned with the generic grading contract and fail fast if
the document is missing.

Contract source: SPEC.md scoring rule + ACTION_PLAN.md Stage 3 acceptance,
with the Selection pilot as builder configuration/validation fixture.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs" / "developers" / "classroom50-autograder.md"
SELECTION_DIR = REPO_ROOT / "exercises" / "selection"

# Pinned pilot expectations (SPEC.md). The collected-count test below
# re-derives these from real pytest collection so the pins cannot drift
# silently from the canonical test sources.
EXPECTED_KEYS: tuple[str, ...] = (
    "ex001_selection_modify_basics",
    "ex002_selection_debug_if_then_else",
    "ex003_selection_modify_elif_boundaries",
    "ex004_selection_modify_logical_operators",
)
EXPECTED_COUNTS: dict[str, int] = {
    "ex001_selection_modify_basics": 33,
    "ex002_selection_debug_if_then_else": 60,
    "ex003_selection_modify_elif_boundaries": 60,
    "ex004_selection_modify_logical_operators": 71,
}
EXPECTED_TITLES: dict[str, str] = {
    "ex001_selection_modify_basics": "Selection Modify Basics",
    "ex002_selection_debug_if_then_else": "Selection Debug If Then Else",
    "ex003_selection_modify_elif_boundaries": (
        "Selection Modify: Elif Chains, Boundaries and Constants"
    ),
    "ex004_selection_modify_logical_operators": "Selection Modify Logical Operators",
}
EXPECTED_TOTAL = 224

_COLLECT_LINE_RE = re.compile(r"^(?P<path>.+?): (?P<count>\d+)\s*$")


def _read_doc() -> str:
    """Read the autograder contract doc, failing fast if it is absent."""
    assert DOC_PATH.is_file(), (
        f"Stage 3 contract document missing: {DOC_PATH.relative_to(REPO_ROOT)}"
    )
    return DOC_PATH.read_text(encoding="utf-8")


def _normalised(text: str) -> str:
    return " ".join(text.lower().split())


def _canonical_test_file(exercise_key: str) -> Path:
    return SELECTION_DIR / exercise_key / "tests" / f"test_{exercise_key}.py"


def _exercise_titles() -> dict[str, str]:
    """Derive the exact Selection titles from the canonical exercise.json sources."""
    titles: dict[str, str] = {}
    for key in EXPECTED_KEYS:
        metadata_path = SELECTION_DIR / key / "exercise.json"
        assert metadata_path.is_file(), f"Canonical metadata missing: {metadata_path}"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        titles[key] = metadata["title"]
    return titles


def _collected_counts() -> dict[str, int]:
    """Derive per-exercise collected pytest counts via collection only.

    Runs pytest with `--collect-only` (no test is executed, no notebooks run,
    no network): the count per file is the number of collected cases, which
    includes parametrize expansion that a plain `def test_` count would miss.
    """
    counts: dict[str, int] = {}
    for key in EXPECTED_KEYS:
        test_file = _canonical_test_file(key)
        assert test_file.is_file(), f"Canonical test file missing: {test_file}"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "no:cacheprovider",
                str(test_file),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert proc.returncode == 0, f"Collection failed for {key}:\n{proc.stderr}"
        match = _COLLECT_LINE_RE.match(proc.stdout.strip().splitlines()[-1])
        assert match is not None, f"Unparseable collect output for {key}:\n{proc.stdout}"
        counts[key] = int(match.group("count"))
    return counts


def _documented_count(doc: str, exercise_key: str) -> int:
    """Extract the case count from the documentation row for one exercise."""
    for line in doc.splitlines():
        if exercise_key not in line:
            continue
        matches = re.findall(r"(?<!\d)(\d{1,3})(?!\d)", line.replace(exercise_key, ""))
        if len(matches) == 1:
            return int(matches[0])
    raise AssertionError(f"Contract must document one case count for {exercise_key}")


def test_contract_doc_exists() -> None:
    assert DOC_PATH.is_file(), (
        "Stage 3 deliverable missing: docs/developers/classroom50-autograder.md does not exist"
    )


def test_scoring_one_point_per_case() -> None:
    doc = _normalised(_read_doc())
    assert "one point per passing pytest case" in doc, (
        "Contract must state one point per passing pytest case"
    )


def test_per_test_names_exact_leaf_nodeid() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    assert "<exercise_key>::" in doc.replace(" ", ""), (
        "Contract must name per-test results as <exercise_key>::<leaf-nodeid>"
    )
    assert "test_*.py::test_name" in doc, (
        "Contract must define the leaf nodeid as test_*.py::test_name"
    )
    assert "no absolute paths" in lowered, "Contract must forbid absolute paths in names"


def test_full_total_computed_and_pilot_counts() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    actual = _collected_counts()
    assert actual == EXPECTED_COUNTS, (
        f"Pinned pilot counts drifted from collected reality: {actual}"
    )
    assert sum(actual.values()) == EXPECTED_TOTAL, "Pilot total must be 224"
    documented = {key: _documented_count(doc, key) for key in EXPECTED_KEYS}
    assert documented == actual, (
        f"Documented pilot counts must match collected pytest counts: {documented} != {actual}"
    )
    assert re.search(r"(?:total|full[- ]pass|max[- ]score)[^\n]*\b224\b", lowered), (
        "Contract must record the 224-case Selection pilot total"
    )
    for key in actual:
        assert key in doc, f"Contract must list pilot exercise key {key}"
    assert "computed" in lowered and "sum" in lowered, (
        "Contract must state the full-pass total is computed as the sum (not hardcoded)"
    )


def test_pilot_titles_match_exercise_json() -> None:
    doc = _read_doc()
    actual_titles = _exercise_titles()
    assert actual_titles == EXPECTED_TITLES, (
        f"Pinned pilot titles drifted from exercise.json: {actual_titles}"
    )
    for key, title in actual_titles.items():
        assert title in doc, f"Contract must record the exercise.json title for {key}: {title!r}"


def test_graded_forces_student_variant_solution_reserved_dry_run() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    assert "pytutor_active_variant=student" in lowered, (
        "Contract must state the graded run forces PYTUTOR_ACTIVE_VARIANT=student"
    )
    assert "student variant" in lowered, "Contract must name the graded student variant"
    assert "solution" in lowered and "dry run" in lowered, (
        "Contract must reserve the solution variant for the dry run"
    )


def test_slug_is_operator_input_not_stored() -> None:
    doc = _normalised(_read_doc())
    assert "slug" in doc, "Contract must cover the assignment slug"
    assert "operator input" in doc, "Contract must state the slug is operator input"
    assert "not stored" in doc, "Contract must state the slug is not stored"


def test_selection_is_fixture_not_special_grader() -> None:
    doc = _read_doc()
    lowered = _normalised(doc)
    assert "selection" in lowered, "Contract must identify the Selection pilot"
    assert "validation fixture" in lowered, (
        "Contract must identify Selection as a validation fixture"
    )
    assert "builder configuration" in lowered or "builder config" in lowered, (
        "Contract must identify Selection as a builder configuration"
    )
    assert re.search(
        r"selection[^.?!\n]{0,120}\bnot\b[^.?!\n]{0,60}special grader",
        lowered,
    ), "Contract must explicitly state that Selection is not a special grader"


def test_no_order_of_teaching_change() -> None:
    lowered = _normalised(_read_doc())
    assert re.search(
        r"no (?:`?orderofteaching(?:\.md)?`? change|"
        r"change to `?orderofteaching(?:\.md)?`?)",
        lowered,
    ), "Contract must explicitly state that there is no OrderOfTeaching change"
