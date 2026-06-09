"""MakeScaffold — exercise type scaffold for make exercises.

Each part produces a markdown prompt + a tagged code cell with a TODO
placeholder for the student to write their solution.

Note that MakeScaffold and ModifyScaffold currently share the same cell
structure.  They are kept as separate classes intentionally — the semantics
of "make something from scratch" vs "modify existing code" may diverge in
future exercise types, and having separate classes makes that divergence
explicit and traceable.
"""

from __future__ import annotations

from typing import Any

from scripts.exercise_scaffolder.base import ExerciseScaffold, make_meta


class MakeScaffold(ExerciseScaffold):
    """Scaffold for make-type exercises.

    Students receive a prompt and write their solution from scratch in the
    tagged code cell.
    """

    # ── Type-specific cells ──────────────────────────────────────────────────

    def _build_exercise_cells(self) -> list[dict[str, Any]]:
        """Return standard exercise cells: markdown prompt + code cell per part."""
        cells: list[dict[str, Any]] = []
        for i in range(1, self.parts + 1):
            exercise_tag = f"exercise{i}"
            cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": make_meta("markdown"),
                    "source": [
                        f"## Exercise {i}\n",
                        "(Write the prompt here.)\n",
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
                        f"# Exercise {i}\n",
                        "# The tests will execute the code in this cell and verify the output.\n",
                        "# Write your code below.\n",
                        "\n",
                        "print('TODO: Write your solution here')\n",
                    ],
                }
            )
        return cells

    # ── Test body assertions ─────────────────────────────────────────────────

    def _build_exercise_body_test_lines(self) -> list[str]:
        """Return test assertions for make exercise body cells.

        Uses the standard TODO-placeholder guard.
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

    # ── README hook ──────────────────────────────────────────────────────────

    def readme_type_hook(self) -> list[str]:
        return []
