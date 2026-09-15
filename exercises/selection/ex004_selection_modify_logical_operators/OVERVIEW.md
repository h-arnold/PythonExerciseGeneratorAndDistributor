# Teaching Notes: Selection Modify — Logical Operators

## Prerequisites
- **Sequence construct**: `input()`, `int()` casting, `print()`, and basic arithmetic (`+`, `*`, `//`, `-`).
- **Selection basics** (ideally `ex001_selection_modify_basics`): `if` and `if`-`else` with `==`, `!=`, `<`, `>`.
- **Boundaries and constants** (ideally `ex003_selection_modify_elif_boundaries`): `<=`, `>=`, and UPPER_CASE constants.
- This set introduces `and`, `or`, and `not`.

## Common Misconceptions
- **"`and` means add the numbers."** Students may read `and` as arithmetic. Stress it joins two true/false questions: both answers must be yes.
- **"`or` means only one."** Clarify that `or` passes when either side (or both) is true — e.g. a score of 55 with attendance of 90 still passes exercise 3.
- **Forgetting to rewrite both messages** — the starter messages describe the old single-check behaviour (e.g. "Warm enough"); the task asks for new messages on both branches.
- **Changing the constants** — from exercise 5 the constants are fixed scaffolding. The task is the branch logic and messages, not the numbers.
- **Brackets in exercise 9** — without brackets, `and` binds tighter than `or` and the discount goes to the wrong pupils. Make the grouping explicit: membership first, then the bracketed either-or.
- **`not` placement** — `not (age < 5)` reverses the whole comparison; `not age < 5` is harder to read. Model the bracketed form used in the solutions.

## Teaching Approach
1. **Start with real-world language**: "You can join if you are 11 or older *and* 16 or younger" maps directly onto exercise 1. Get pupils saying the `and`/`or` sentence before touching code.
2. **Exercises 1–4 use no constants on purpose** — keep attention on the operator word being added or swapped. Constants return in exercise 5 once the words feel natural.
3. **Prove each change with two runs**: one input where starter and solution agree, one where they differ (the expected-output input). Every solution diverges from its starter on the given input — use that contrast in class.
4. **For exercise 9**, draw the logic as a gate diagram: membership AND (spending OR age). Then show the brackets mirror the diagram.
5. **Exercise 10 is the stretch goal**: discount lines first, then gold, then silver. Weaker pupils can stop after the discount and still show progress.

## Differentiation
- **Stretch**: ask students to add a third free museum group in exercise 6, or a new loyalty tier in exercise 10, using a new constant.
- **Support**: for exercises 1–4, name the exact line to change ("the `if` line") and let pupils focus on the single operator word; the scenario line already explains *why* the change is needed.
