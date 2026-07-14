# Selection Modify: Elif Chains, Boundaries and Constants — ex003

## Learning Objective
Modify existing `if` / `elif` / `else` programs to introduce the boundary operators `<=` (less than or equal to) and `>=` (greater than or equal to), refactor fixed values into UPPER_CASE **constants**, and change constant values, operators, and output messages. Every printed message uses an **f-string**, and arithmetic (`+`, `*`, `//`, `%`, `round()`) is used inside the conditions.

## Notebook Path
- Student: `notebooks/student.ipynb`
- Solution: `notebooks/solution.ipynb`

## Tests Path
- Canonical tests: `tests/test_ex003_selection_modify_elif_boundaries.py` (authored in Phase 2 by the Exercise Test Creator)

## Summary
Ten modification exercises. Exercises 1–3 are gentle **refactors**: students rewrite working `if`/`elif`/`else` code so that fixed thresholds are stored in named constants (e.g. `FREE_DELIVERY_THRESHOLD = 50`), with no change in behaviour. From exercise 4 the code already uses constants and students must change the constant's **value** and/or the **operator**, as well as the messages, while keeping the `elif` chain intact. Difficulty ramps from a single `if`/`elif`/`else` (ex1–3), through `if`/`elif`/`else` with arithmetic (ex4–5), to one-`elif` (ex6–7), two-`elif` (ex8), three-`elif` (ex9), and a multi-`elif` chain that also changes the cost formula (ex10).

## New concepts introduced here
- Boundary operators `<=` and `>=` (the `Selection Cheat Sheet` only covered `==`, `!=`, `<`, `>` before this set).
- Storing fixed values in **constants** written in UPPER_CASE (see `../additional-resources/constants-intro.md`).

## Teacher notes
- Created: 2026-07-14
- Exercise type: Modify (students edit working code in place)
- Construct: `selection` (prerequisite: `sequence` — `input()`, `int()`, `print()`, and all arithmetic operators from the Arithmetic Cheatsheet)
- Linked reference: [Introduction to Constants](../additional-resources/constants-intro.md)
- Tests are intentionally NOT written yet (Phase 2). Student-variant behaviour currently fails until tests are added; the solution notebook passes all expected outputs (verified manually).
