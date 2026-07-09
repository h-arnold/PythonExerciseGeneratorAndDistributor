# Overview — Sequence Make Consolidation

## Prerequisites

Before attempting this exercise, students should be comfortable with:

- `print()` for exact output
- Creating and using variables (strings, integers, floats)
- `input()` to read text from the user
- String concatenation using `+`
- f-strings for formatted output
- Arithmetic operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- `round()` for rounding numbers
- Casting with `int()`, `float()`, and `str()`
- The ceiling-division pattern `(total + pack_size - 1) // pack_size`
- Power (`** 2`) and square root (`** 0.5`)

Recommended prior exercises: ex002–ex014 in order.

## Common Misconceptions

1. **String vs number confusion**: Students may try to concatenate numbers directly into strings without using f-strings, `str()`, or commas. Remind them that f-strings handle this automatically.

2. **Forgetting to cast `input()`**: Since `input()` always returns a string, students must convert with `int()` or `float()` before doing arithmetic. Watch for `TypeError` in exercises 3–10.

3. **Integer vs float division**: Students may use `/` when `//` is needed (e.g., distributing items among people). Prompt them to think: "Should the answer be a whole number or a decimal?"

4. **Rounding confusion**: `round(x, 2)` rounds to 2 decimal places but won't add trailing zeros (e.g. `round(72.5, 2)` is `72.5`, not `72.50`). These exercises use `round(value, 2)` for money values, so the expected output shows the natural number of decimal places — students should not add trailing zeros and should not use the `:.2f` format specifier.

5. **Ceiling division pattern**: The formula `(total + pack_size - 1) // pack_size` (used in exercises 2 and 10) is non-intuitive. Model it with small numbers first (e.g., 10 items in packs of 6: `(10 + 6 - 1) // 6 = 15 // 6 = 3`), explaining that it always rounds up.

6. **Reading the expected output exactly**: Exercises test exact output, including punctuation and spacing. Encourage students to copy-paste the expected output as a reference while building their `print()` statements.

7. **Self-contained cells**: Each tagged cell runs independently. A common mistake is to define a variable in exercise 3 and try to use it in exercise 4. Remind students that each cell starts fresh.

## Teaching Approach and Hints

### Suggested delivery (50–60 minute lesson)

| Phase | Time | Activity |
|---|---|---|
| Warm-up | 5 min | Review floor division `//` and modulus `%` with quick examples on the board |
| Model | 10 min | Work through Exercise 1 together as a class — read the prompt, plan the variables, write the code step by step |
| Pair/Independent | 25 min | Students work through exercises 2–7 at their own pace; circulate to help |
| Challenge | 15 min | Direct students to exercises 8–10; encourage stronger students to attempt 9–10 without hints |
| Wrap-up | 5 min | Run the self-check cell and celebrate progress |

### Scaffolding strategies

- **If a student is stuck on exercise 1**: Point to each step in the algorithm and ask "What variable stores this number?" and "What operator do you use?"
- **If a student is stuck on exercise 4**: Ask "If I have 3 pizzas, how many slices is that? What arithmetic gives you that answer?"
- **If a student is stuck on exercise 10**: Suggest they break the problem into four parts: total pencils, pencil packs, total erasers, eraser packs. Solve each part before worrying about the final `print()`.

### Extension ideas

For students who finish early:
- Challenge them to add input validation (e.g., reject negative numbers) — but remind them this is preview material for the selection construct.
- Ask them to re-write one exercise output using string concatenation (`+`) instead of f-strings, or vice versa.
- Have them write an exercise 11 for the notebook that combines two of the concepts (e.g., a bill splitter that also calculates the tip as a percentage of the per-person share).

## Suggested Worked Examples (board-ready)

### Worked Example A — Ceiling Division (for Exercise 2)

Problem: 15 square metres of wall, 12 m² per can of paint.
- `(15 + 12 - 1) // 12 = 26 // 12 = 2 cans`
- Unused: `(2 × 12) - 15 = 9 m²`

### Worked Example B — Square Root (for Exercise 8)

Problem: Garden side = 5 m, area = 5² = 25 m².
- Double: 50 m²
- New side = 50**0.5 = 7.071... → rounded to 2 d.p. = 7.07 m

## Expected Progression

| Exercise | Input | Output type | Key skill |
|---|---|---|---|
| 1 | None | Static | `//`, `%`, f-strings |
| 2 | None | Static | Ceiling division, multi-line output |
| 3 | 1 int | Dynamic | `int(input())`, simple arithmetic |
| 4 | 2 ints | Dynamic | `//`, `%` with input |
| 5 | 2 floats | Dynamic | `float(input())`, `round(..., 2)` |
| 6 | 1 int | Dynamic | Formula with `/`, `round()` |
| 7 | 2 ints | Dynamic | `//`, `%` with larger numbers |
| 8 | 1 int | Dynamic | `** 2`, `** 0.5`, `round()` |
| 9 | 2 floats + 1 int | Dynamic | Multi-step calculation, `round(..., 2)` |
| 10 | 3 ints | Dynamic | Multi-step ceiling division |
