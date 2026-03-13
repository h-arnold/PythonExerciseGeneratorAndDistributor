# Teaching Notes: Casting and Type Conversion (ex006)

## Prerequisites

- Students should understand basic `print()` statements and variable assignment.
- Students should be familiar with `input()` returning text.

## Common Misconceptions

- Adding numeric strings without casting them first joins the text instead of adding the numbers.
- Choosing `int()` when the task needs a decimal result loses precision.
- Forgetting to convert numbers back to `str()` before concatenating them into output text causes errors.

## Teaching Approach

1. Demonstrate that `input()` always produces a string, even when the learner types digits.
2. Contrast `int()` and `float()` on short examples before students edit the notebook cells.
3. Encourage students to make one change at a time, run the cell, and compare the output with the expected result.

## Hints

- Ask students to say what type each variable holds before they change the code.
- Model explicit intermediate variables when a conversion step feels confusing.
- Remind students that output text often needs `str()` even after the arithmetic is correct.
