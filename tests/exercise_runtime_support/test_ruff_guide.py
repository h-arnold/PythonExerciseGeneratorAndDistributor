"""Regression checks for the student-facing Ruff guide and its examples."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from exercise_runtime_support.student_checker.readability import analyze_source

_GUIDE_PATH = (
    Path(__file__).resolve().parents[2] / "template_repo_files" / "fixing-readability-issues.md"
)
_POLICY_CODES = {
    "E101",
    "E111",
    "E117",
    "E225",
    "E226",
    "E227",
    "E228",
    "E231",
    "E501",
    "E741",
    "N802",
    "N803",
    "N806",
    "N816",
    "W191",
    "W291",
    "W293",
}
_SECTION = re.compile(r"^### (E\d{3}|N\d{3}|W\d{3})\b.*$", re.MULTILINE)
_FENCE = re.compile(r"```python[ \t]*\r?\n(.*?)\r?\n```", re.DOTALL)
_ANCHOR = re.compile(r'<a id="(e\d{3}|n\d{3}|w\d{3})"></a>')
_INDEX_HEADING = re.compile(r"^## Code index[ \t]*$", re.MULTILINE)
_NEXT_SECTION = re.compile(r"^## (?!#).*$", re.MULTILINE)
_INDEX_LINK = re.compile(r"\[([ENW]\d{3})\]\(#([enw]\d{3})\)")


def _read_guide() -> str:
    return _GUIDE_PATH.read_text(encoding="utf-8")


def _rule_sections(guide: str) -> dict[str, str]:
    matches = list(_SECTION.finditer(guide))
    codes = [match.group(1) for match in matches]
    assert len(codes) == len(set(codes)), "Rule headings must not be duplicated"
    return {
        code: guide[
            match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(guide)
        ]
        for index, (code, match) in enumerate(zip(codes, matches, strict=True))
    }


def _example(section: str, label: str) -> str:
    label_match = re.search(rf"\*\*{re.escape(label)}\*\*", section, re.IGNORECASE)
    assert label_match is not None, f"Missing labelled {label}"
    fence = _FENCE.search(section, label_match.end())
    assert fence is not None, f"{label} must be followed by a fenced python example"
    return fence.group(1)


def _visible_whitespace(source: str) -> str:
    return source.replace("<TAB>", "\t").replace("<SPACE>", " ")


def test_python_fence_extraction_preserves_initial_whitespace() -> None:
    section = "**Non-example**\n```python\n   \n```"

    assert _example(section, "Non-example") == "   "


def test_guide_rule_anchors_and_code_index_match_the_selected_policy() -> None:
    guide = _read_guide()
    sections = _rule_sections(guide)
    headings = list(_SECTION.finditer(guide))
    anchors = [anchor.group(1) for anchor in _ANCHOR.finditer(guide)]
    index_heading = _INDEX_HEADING.search(guide)
    assert index_heading is not None
    next_heading = _NEXT_SECTION.search(guide, index_heading.end())
    index = guide[index_heading.end() : next_heading.start() if next_heading else len(guide)]
    links = _INDEX_LINK.findall(index)

    assert set(sections) == _POLICY_CODES
    assert len(sections) == len(_POLICY_CODES)
    assert set(anchors) == {code.lower() for code in _POLICY_CODES}
    assert len(anchors) == len(_POLICY_CODES)
    assert len(links) == len(_POLICY_CODES)
    assert {label for label, _ in links} == _POLICY_CODES
    assert all(label.lower() == target for label, target in links)
    for code, heading in zip((match.group(1) for match in headings), headings, strict=True):
        anchor = f'<a id="{code.lower()}"></a>'
        heading_text = heading.group(0)
        before = re.search(rf"{re.escape(anchor)}\r?\n{re.escape(heading_text)}", guide)
        after = re.search(rf"{re.escape(heading_text)}\r?\n{re.escape(anchor)}", guide)
        assert before or after


@pytest.mark.parametrize("code", sorted(_POLICY_CODES))
def test_rule_examples_include_the_advertised_finding_and_clean_correction(code: str) -> None:
    section = _rule_sections(_read_guide())[code]
    non_example = _visible_whitespace(_example(section, "Non-example"))
    corrected = _visible_whitespace(_example(section, "Corrected example"))

    ast.parse(non_example)
    actual = analyze_source(non_example, cell_index=0, task_tag="exercise1")
    repaired = analyze_source(corrected, cell_index=0, task_tag="exercise1")
    assert code in {finding.code for finding in actual.findings}
    assert not repaired.findings
    if code == "E101":
        assert not actual.syntax_blocked
