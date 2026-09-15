# Selection Modify: Logical Operators — ex004

## Learning Objective
Modify existing `if` / `elif` / `else` programs to combine comparisons with the logical operators `and`, `or`, and `not` (including bracketed groups such as `member == "yes" and (spend >= SPEND_LIMIT or age >= SENIOR_AGE)`). Every printed message uses an **f-string**; fixed values from exercise 5 onward are stored in UPPER_CASE **constants**.

## Notebook Path
- Student: `notebooks/student.ipynb`
- Solution: `notebooks/solution.ipynb`

## Tests Path
- Canonical tests: `tests/test_ex004_selection_modify_logical_operators.py` (authored in Phase 2 by the Exercise Test Creator)

## Summary
Ten modification exercises. Exercises 1–4 deliberately use no constants so the focus stays purely on the operators: add `and` to check both ends of an age range (ex1), add `or` for the whole weekend (ex2), swap `and` for `or` so either a score or attendance target passes (ex3), and flip a check with `not` (ex4). From exercise 5 constants return and stay fixed throughout — students change only the branch logic and messages: comfortable temperature band (ex5, `and`), second free museum group (ex6, `or`), gold band on a computed total (ex7, `and`), film club age plus attitude (ex8, `and` with `not`), member discount with a bracketed either-or (ex9, `and`/`or`), and cinema loyalty tiers with a tenth-off discount plus mixed operators in an `elif` chain (ex10, hardest).

## New concepts introduced here
- Logical operators `and`, `or`, and `not` for combining comparisons.
- Grouping with brackets to control `and`/`or` precedence (exercise 9).
- Using `not` to express the reverse of a check (exercises 4, 8, 10).

## Teacher notes
- Created: 2026-09-15
- Exercise type: Modify (students edit working code in place)
- Construct: `selection` (prerequisite: `sequence` — `input()`, `int()`, `print()` — plus `ex001` selection basics and `ex003` boundary operators and constants)
- Tests are intentionally NOT written yet (Phase 2). Student-variant behaviour currently fails until tests are added; the solution notebook passes all expected outputs (verified manually).
