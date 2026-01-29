# Sequence Modify Variables (ex003)

## Prerequisites
- Comfort with running the notebook and using `print()` to show text on screen.
- Practice from the previous modify set so students recognise working code that must be adjusted rather than written from scratch.

## Expected student misconceptions
- Editing the wrong part of the code (e.g., changing the `print()` text instead of the variable assignment) and wondering why the output still uses the old value.
- Forgetting to keep a space when joining variables and seeing words run together.
- Assuming `input()` prints the typed text automatically rather than storing it in a variable that the next line must use.

## Suggested worked examples
- Walk through Exercise 1 live, changing the `greeting` assignment and rerunning so students see how the `print()` output follows the variable value.
- For the first input exercise, show how to run the cell while the prompt prints and how a placeholder value (e.g., typing "mango") is caught by `input()` and used immediately.

## Teaching notes
- Keep the focus on editing a single line per step; encourage students to read the expected output before making the change.
- When demonstrating concatenation, highlight how each variable contributes one piece of the sentence and the `+` operator simply joins them together.
- Use the optional self-check cell (at the bottom of the notebook) to trial extra strings if a student wants to practise more before re-running the tests.
- Later parts of the exercise (ex4-ex6) require students to use two input() calls to build the final message; teachers may demonstrate concatenation with + and show sample inputs.
