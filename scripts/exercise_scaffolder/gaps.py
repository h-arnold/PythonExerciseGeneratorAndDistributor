"""GapsScaffold — exercise type scaffold for gap-fill exercises.

Each part produces a markdown-description + a tagged code cell with a
``# YOUR CODE HERE`` comment that the student must replace with their
solution.
"""

from __future__ import annotations

from typing import Any

from scripts.exercise_scaffolder.base import ExerciseScaffold, make_meta


class GapsScaffold(ExerciseScaffold):
    """Scaffold for gaps-type exercises.

    Students receive partially written code with a ``# YOUR CODE HERE``
    comment marking the line(s) they need to write.
    """

    # ── Type-specific cells ──────────────────────────────────────────────────

    @property
    def _cells_per_exercise(self) -> int:
        return 2  # markdown + code

    def _build_exercise_cells(self) -> list[dict[str, Any]]:
        """Return gap-fill exercise cells: description + code cell per part."""
        cells: list[dict[str, Any]] = []
        for i in range(1, self.parts + 1):
            exercise_tag = f"exercise{i}"
            cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": make_meta("markdown"),
                    "source": [
                        f"## Exercise {i}\n",
                        "(Describe the task and show the expected output here.)\n",
                        "\n",
                        "**Expected output:**\n",
                        "```\n",
                        "(put expected output here)\n",
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
                        f"# Exercise {i} — replace this scaffold with the real "
                        f"partially-written program.\n",
                        "# Keep the YOUR CODE HERE comment where the student "
                        "must write their line(s).\n",
                        "\n",
                        "# YOUR CODE HERE\n",
                    ],
                }
            )
        return cells

    # ── Test body assertions ─────────────────────────────────────────────────

    def _build_exercise_body_test_lines(self) -> list[str]:
        """Return test assertions for gaps exercise body cells.

        Uses gaps-style guard: verifies cell produced output (no TODO check).
        """
        if self.parts == 1:
            return [
                "def test_exercise1_output() -> None:",
                "    output = _run_and_capture('exercise1')",
                "    # TODO: Add assertions to verify the output",
                "    assert output.strip(), "
                "'Cell produced no output - fill in the # YOUR CODE HERE line(s) and re-run'",
                "    # Example: assert 'expected text' in output",
                "",
            ]

        exercise_tags = ", ".join(f"'exercise{i}'" for i in range(1, self.parts + 1))
        return [
            f"@pytest.mark.parametrize('tag', [{exercise_tags}])",
            "def test_exercise_cells_execute(tag: str) -> None:",
            '    """Verify each tagged cell executes without error."""',
            "    output = _run_and_capture(tag)",
            "    assert output.strip(), "
            "f'{tag}: Cell produced no output - fill in the # YOUR CODE HERE line(s) and re-run'",
            "",
        ]

    # ── README hook ──────────────────────────────────────────────────────────

    def readme_type_hook(self) -> list[str]:
        return [
            "- Find the `# YOUR CODE HERE` comment in each tagged cell and write the "
            "missing line(s) of code in its place.",
        ]
