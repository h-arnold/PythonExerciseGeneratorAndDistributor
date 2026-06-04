# Teaching Notes: Sequence Modify Maths Operators (ex012)

## Prerequisites

- Students can read and edit short sequence programs with variables.
- Students understand basic arithmetic operators (`+`, `-`, `*`, `/`).
- Students know how to use `print()` and `str()` for output.
- Students have practised f-strings from ex009–ex011.

## Common misconceptions

- Confusing `/` (true division) with `//` (floor division) — `//` drops the decimal part entirely rather than rounding.
- Forgetting that `%` returns the *remainder*, not the quotient — `29 % 4` is `1` (the leftover), not `7` (the number of groups).
- Treating `round()` as truncation — `round(6.666, 1)` gives `6.7` (rounded), not `6.6` (truncated).
- Applying the wrong operator to the wrong part of a multi-step problem (e.g., using `//` where `%` is needed and vice versa).

## Suggested teaching flow

1. Introduce floor division and modulus together using a physical grouping example (e.g., 29 students into groups of 4 — 7 full groups, 1 left over).
2. Let learners complete exercises 1–4 as confidence builders: single-operator changes.
3. Pause before exercise 5 to introduce `round(value, places)` with a money example.
4. Use exercises 5–6 as straightforward rounding practice.
5. Exercises 7–8 combine `//` and `%` in the same program — model one conversion together first.
6. Exercise 9 is a quick rounding refresher.
7. Exercise 10 is the mixed challenge — all three operators in one program.

## Suggested hints

- Hint 1: `//` gives the whole number of groups; `%` gives what is left over.
- Hint 2: If your answer has a decimal point where it should not, you probably used `/` instead of `//`.
- Hint 3: `round(value, 2)` rounds to 2 decimal places — useful for money.
- Hint 4: For the mixed challenge, fix one calculation at a time and check the output before moving to the next.

## Why this exercise exists

This set introduces integer-division and remainder semantics alongside controlled rounding, extending earlier arithmetic work to operators that are essential for A-Level Computer Science. Students edit working code to replace plain division and placeholder values with the correct operators, reinforcing the idea that different division operators serve different real-world purposes.
