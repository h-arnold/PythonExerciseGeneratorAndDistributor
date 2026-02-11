# Overview - Data Types Debug Casting

## Prerequisites
- Understand that `input()` returns a string.
- Know the difference between `int`, `float`, and `str`.
- Be able to use basic arithmetic and string concatenation.

## Common misconceptions to address
- Forgetting to convert user input before doing arithmetic.
- Using `int()` when a decimal result is required.
- Mixing strings and numbers in `+` without converting.
- Using `//` when a precise average is needed.

## Teaching approach and hints
- Encourage students to read error messages and identify the type mismatch.
- Ask: "What type is this value right now?" before each calculation.
- Model step-by-step conversions using intermediate variables.
- Suggest fixing one line at a time and re-running the cell.

## Suggested worked examples
- A simple "age next year" example using `int(input())` and `str()` for output.
- Converting pounds and pence to total pence with `int()`.
- Average of two numbers using `/` instead of `//`.

## Expected progression
- Exercises 1-5: single casting mistakes in short sequences.
- Exercises 6-10: multiple coordinated issues with input, arithmetic, and output.
