# Teaching Notes: Sequence Debug Syntax (ex004)

## Prerequisites
- Students should know: basic `print()` usage, string literals, simple arithmetic, and how to read error messages.
- Prior exercises: `ex002_sequence_modify_basics`, `ex003_sequence_modify_variables`.

## Common Misconceptions
- Missing parentheses or quotes cause syntax errors; students may not spot the missing character.
- Students often forget that string concatenation requires the `+` operator between each part.
- `input()` always returns a string, so no type casting is needed for string concatenation.

## Teaching Approach
1. Demonstrate reading a Python SyntaxError and locating the line with the problem.
2. For each buggy example, ask students to explain the error first (short written explanation), then fix and run it.
3. Exercise 7 focuses on string concatenation syntax: students must add `+` operators between string parts. This reinforces that concatenation requires explicit operators in Python.

## Hints
- Encourage students to run one cell at a time and read the error trace.
- For Exercise 7, remind students that Python needs `+` to join strings together (e.g., `"Hello " + name`).
