# Teaching Notes: Sequence Modify F-Strings (ex009)

## Prerequisites

- Students can read and edit short sequence programs with variables.
- Students have practised string concatenation with `+`.
- Students know `input()` returns text and can be converted with `int()` or `float()`.
- Students can perform basic arithmetic with `+` and `*`.

## Common misconceptions

- Forgetting the `f` before the opening quote in an f-string.
- Writing variable names directly in text instead of inside `{}`.
- Leaving old concatenation fragments while partially rewriting to f-strings.
- Changing output text correctly but forgetting to fix the arithmetic logic.

## Suggested teaching flow

1. Model one quick conversion from concatenation to f-string on the board.
2. Let learners complete exercises 1-3 as confidence builders around changing existing f-string text.
3. Pause after exercise 7 to review how f-strings remove the need for `str()` in output lines.
4. Use exercises 8-10 as logic-plus-output checks where arithmetic and text must both be correct.

## Suggested hints

- Hint 1: Start by matching the expected output exactly, including punctuation.
- Hint 2: If you see `+` in a `print()` line, try replacing the whole line with one f-string.
- Hint 3: For the final three tasks, calculate the correct value in a variable first, then print that variable in the f-string.

## Why this exercise exists

This set bridges earlier sequence work (concatenation, input, and arithmetic) to a newer output style (f-strings) without introducing later constructs such as selection, iteration, or functions.
