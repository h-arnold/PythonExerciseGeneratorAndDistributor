"""DebugScaffold — exercise type scaffold for debug exercises.

Each part produces a markdown-description + buggy-code cell tagged
``exerciseN`` + explanation markdown cell tagged ``explanationN``.
"""

from __future__ import annotations

from typing import Any

from scripts.exercise_scaffolder.base import ExerciseScaffold, make_meta


class DebugScaffold(ExerciseScaffold):
    """Scaffold for debug-type exercises.

    Students receive buggy code that they must correct, then explain
    what they fixed in an explanation cell.
    """

    # ── Type-specific cells ──────────────────────────────────────────────────

    @property
    def _cells_per_exercise(self) -> int:
        return 3  # markdown + code + explanation

    def _build_exercise_cells(self) -> list[dict[str, Any]]:
        """Return debug exercise cells: description + buggy code + explanation."""
        cells: list[dict[str, Any]] = []
        for i in range(1, self.parts + 1):
            exercise_tag = f"exercise{i}"
            explanation_tag = f"explanation{i}"
            cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": make_meta("markdown"),
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
                    "metadata": make_meta("python", tags=[exercise_tag]),
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
                    "metadata": make_meta("markdown", tags=[explanation_tag]),
                    "source": [
                        "### What actually happened\n",
                        "Describe briefly what happened when you ran the code "
                        "(include any error messages or incorrect output).\n",
                    ],
                }
            )
        return cells

    # ── Test body assertions ─────────────────────────────────────────────────

    def _build_exercise_body_test_lines(self) -> list[str]:
        """Return test assertions for debug exercise body cells.

        Uses the standard TODO-placeholder guard (not gaps-style).
        """
        if self.parts == 1:
            return [
                "def test_exercise1_output() -> None:",
                "    output = _run_and_capture('exercise1')",
                "    # TODO: Add assertions to verify the output",
                "    assert output.strip(), 'Exercise should produce output'",
                "    assert 'TODO' not in output, "
                "'Replace the TODO placeholder with your solution'",
                "    # Example: assert 'expected text' in output",
                "",
            ]

        exercise_tags = ", ".join(f"'exercise{i}'" for i in range(1, self.parts + 1))
        return [
            f"@pytest.mark.parametrize('tag', [{exercise_tags}])",
            "def test_exercise_cells_execute(tag: str) -> None:",
            '    """Verify each tagged cell executes without error."""',
            "    output = _run_and_capture(tag)",
            "    assert output.strip(), f'{tag} should produce output'",
            "    assert 'TODO' not in output, f'Replace the TODO placeholder in {tag}'",
            "",
        ]

    # ── Type-specific test helpers (debug explanation checks) ────────────────

    def _build_type_specific_test_lines(self) -> list[str]:
        """Return debug explanation cell check lines."""
        lines = ["# Explanation cell checks for debug exercises", ""]
        if self.parts == 1:
            lines.extend(
                [
                    "def test_explanation_has_content() -> None:",
                    "    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag='explanation1')",
                    "    assert is_valid_explanation(",
                    "        explanation,",
                    "        min_length=_MIN_EXPLANATION_LENGTH,",
                    "        placeholder_phrases=_PLACEHOLDER_PHRASES,",
                    "    )",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    f"EXPLANATION_TAGS = [f'explanation{{i}}' for i in range(1, {self.parts} + 1)]",
                    "@pytest.mark.parametrize('tag', EXPLANATION_TAGS)",
                    "def test_explanations_have_content(tag: str) -> None:",
                    "    explanation = get_explanation_cell(_NOTEBOOK_PATH, tag=tag)",
                    "    assert is_valid_explanation(",
                    "        explanation,",
                    "        min_length=_MIN_EXPLANATION_LENGTH,",
                    "        placeholder_phrases=_PLACEHOLDER_PHRASES,",
                    "    )",
                    "",
                ]
            )
        return lines

    # ── README hook ──────────────────────────────────────────────────────────

    def readme_type_hook(self) -> list[str]:
        return [
            "- After running your corrected solution, describe what happened in the cell "
            "tagged `explanation1` (or `explanationN`).",
        ]
