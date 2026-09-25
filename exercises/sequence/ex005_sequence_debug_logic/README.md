# ex005: Sequence Debug Logic

## Metadata

- **ID**: ex005
- **Title**: Debug Logical Errors in Sequence Programs
- **Construct**: Sequence (basic input, output, calculations)
- **Type**: Debug
- **Difficulty**: Easy to Medium
- **Learning objective**: Identify and fix logical errors in simple sequential programs using only basic Python constructs (print, input, variables, arithmetic, string operations)

## Files

- **Notebook path inside this exercise folder**: `notebooks/student.ipynb`
- **Solution path inside this exercise folder**: `notebooks/solution.ipynb`
- **Tests path inside this exercise folder**: `tests/test_ex005_sequence_debug_logic.py`

## Structure

This is a 10-part debugging exercise focusing on **logical errors** (not syntax errors):

- **Exercises 1-5**: Single logical error each (wrong operator, wrong variable, missing space, etc.)
- **Exercises 6-9**: Multiple logical errors; Exercises 6, 7, and 9 contain two live errors, while Exercise 8 requires three spacing fixes
- **Exercise 10**: One missing-space bug in a longer input message

## Common Bugs Covered

1. Wrong arithmetic operator (`+` instead of `*`, `/` instead of `*`, etc.)
2. Using the wrong variable
3. Missing spaces in string concatenation
4. Confusing text values read with `input()` in a message
5. Wrong order of operands in subtraction
6. Incorrect formula or missing terms in calculations
7. Printing the wrong variable

## Grading Contract

- Each tagged exercise cell must remain straight-line code: assignments followed by one final positional `print()` payload. Branches, loops, functions, imports, augmented assignments, named expressions, subscripts, attributes, and rebinding built-ins are rejected.
- Exercises 4, 5, 8, and 10 require the taught `+` string concatenation and the exact scaffold variables that feed the message. F-strings are introduced later and are not accepted here.
- Exercise 6 accepts `paid - cost`, `abs(cost - paid)`, or `abs(paid - cost)`.
- Exercise 9 accepts algebraically equivalent perimeter expressions, including `length + length + width + width`, `2 * length + 2 * width`, and `2 * (length + width)`.
- Exercises 5 and 10 are checked with more than one deterministic input case, and their printed results must use the values read from `input()`.
- Explanation cells must contain at least 50 characters and must not be placeholders. Output from untagged scratch cells is ignored by grading.

## Student Instructions

Students should:

1. Read the expected output
2. Run the buggy code to see what actually happens
3. Identify what's wrong
4. Fix the code
5. Write a brief explanation of the bug
6. From the repository root, run `uv run python scripts/run_pytest_variant.py --variant student exercises/sequence/ex005_sequence_debug_logic/tests/test_ex005_sequence_debug_logic.py -q` to verify your fixes, then use `--variant solution` to check the reference solution

## Teaching Notes

See `OVERVIEW.md` in this directory for detailed pedagogical guidance.
