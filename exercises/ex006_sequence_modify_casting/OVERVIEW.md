# Overview — Casting and Type Conversion (ex006)

## Prerequisites
- Students should be comfortable with `print()` and `input()`.
- They should understand basic arithmetic and variable assignment.

## Expected misconceptions
- Believing `input()` returns a number (it returns a string).
- Using `bool()` on textual input like "False" which becomes `True` (non-empty strings are truthy).
- Forgetting to convert numbers to `str` when concatenating with text.

## Suggested worked examples
- Show `age = input()` then `print(age + 1)` fails — demonstrate `int(age)` instead.
- Demonstrate `float()` for decimals, and `str()` for safe concatenation.

## Teaching notes
- Start the lesson by displaying the cheat sheet to learners and run Exercise 1 together as a class demonstration.
- Encourage students to test their programs using the example inputs in the prompts.
- Keep the first four exercises as quick wins (single small change). Exercises 5–10 combine more than one casting step.
