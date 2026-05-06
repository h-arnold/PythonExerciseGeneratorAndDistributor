# Teaching Notes: Sequence Debug F-Strings (ex010)

## Prerequisites

- Students can read and edit short sequence programs with variables.
- Students have completed the f-string modification work in `ex009_sequence_modify_fstrings`.
- Students know that `input()` stores text that can be placed into output messages.
- Students can perform basic arithmetic with `+` and `*`.

## Common misconceptions

- Forgetting the `f` before an f-string.
- Leaving a variable name outside `{}` so plain text is printed instead of the value.
- Using the wrong variable name inside an f-string.
- Fixing the final message but forgetting to repair the calculation first.

## Suggested teaching flow

1. Revisit one example from the modify f-strings exercise and ask pupils to predict what happens if the `f` is removed.
2. Let pupils complete exercises 1-5 independently because each one has a single main bug.
3. Pause after exercise 7 and review the idea that exact wording and punctuation matter, not just the number.
4. Use exercises 8-10 to model a debugging routine: check the variables, check the calculation, then check the final f-string.

## Suggested hints

- Ask pupils to read the expected output aloud and compare it with the actual output line by line.
- Encourage them to fix one line at a time and rerun the code.
- Prompt with: "Is this meant to be text, or should it be the value from a variable?"
- For the final exercises, ask: "Does the calculation happen before the value is printed?"

## Why this exercise exists

This set follows the sequence f-string modification notebook by shifting pupils from editing working code to diagnosing broken code. It stays within the sequence construct while strengthening their accuracy with output, input, variables, and simple arithmetic.