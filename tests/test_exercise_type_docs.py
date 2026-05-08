from pathlib import Path

FILES = {
    "docs/exercise-types/debug.md": "Debugging Exercise Formats",
    "docs/exercise-types/modify.md": "Modification Exercise Formats",
    "docs/exercise-types/make.md": "Make Exercise Formats",
    "docs/exercise-types/gaps.md": "Gap-Fill Exercise Formats",
}


def test_exercise_type_docs_exist_and_have_headings():
    for path, heading in FILES.items():
        p = Path(path)
        assert p.exists(), f"Missing expected file: {path}"
        text = p.read_text(encoding="utf-8")
        assert heading in text, f"Expected heading '{heading}' in {path}"


def test_agent_requires_opening_guides():
    p = Path(".github/agents/exercise_generation.md.agent.md")
    assert p.exists(), "Agent instruction file missing"
    text = p.read_text(encoding="utf-8")
    assert "MUST" in text, "Expected 'MUST' in agent instructions"
    assert "docs/exercise-types/debug.md" in text
    assert "docs/exercise-types/modify.md" in text
    assert "docs/exercise-types/make.md" in text
    assert "docs/exercise-types/gaps.md" in text
    assert "open and follow" in text or "open and follow the" in text
