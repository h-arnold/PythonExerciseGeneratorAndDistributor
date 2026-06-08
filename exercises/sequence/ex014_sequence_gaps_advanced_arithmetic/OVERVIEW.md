# Overview — Advanced Arithmetic Operators (ex014)

## Prerequisites
Students should already be comfortable with:
- Variables, `print()`, and f-strings
- `input()` and `int()` / `float()` casting
- Basic arithmetic (`+`, `-`, `*`, `/`)
- The concept of a program as a sequence of instructions (Sequence construct)

## What this exercise teaches
- The `**` operator for squaring (`n ** 2`), cubing (`n ** 3`), square root (`n ** 0.5`), and arbitrary powers (`base ** exponent`)
- Using `input()` with the split-cast pattern (`x_input = input(...)` then `x_int = int(x_input)`)
- Applying `**` in real-world contexts (area of a square, volume of a cube, area of a circle)
- Using named constants (`pi = 3.14159`)

## Common misconceptions to watch for
1. **`**` vs `^`**: Students may try to use `^` for exponentiation (as in some calculators). The `^` operator in Python is bitwise XOR, not power. Remind them that `**` is the power operator.
2. **Square root confusion**: Students may look for a `sqrt` function or expect `** 0.5` to behave differently. Emphasise that `n ** 0.5` is the same as "the square root of n".
3. **Forgetting to cast**: After exercises 3-5 where casting is demonstrated, students may still forget to cast in exercises 6-10. The `NameError` or `TypeError` they get is the intended signal.
4. **`float` vs `int`**: Students may use `int()` where `float()` is needed (e.g., exercise 5 with decimal side lengths) or vice versa. The expected output decimal places will reveal the mistake.
5. **Variable name confusion**: In later exercises, students must invent their own variable names. Watch for mismatches between the variable they create and the variable used in the provided `print()` line.

## Suggested teaching approach
1. **Introduce `**` with simple examples**: Start by showing `2 ** 3`, `5 ** 2`, `9 ** 0.5` on the board or in a live demo before students open the notebook.
2. **Work through exercises 1-2 together**: These are single-line gaps with hardcoded values — quick wins that build confidence.
3. **Pause at exercise 3**: Point out the split-cast pattern (`number_input` → `number_int`). Explain why each step is separate.
4. **Let students attempt 4-5 independently**: They've seen the pattern; now they apply it with different types (`int` vs `float`).
5. **Exercises 6-10 as a challenge**: By this point students have all the tools. Encourage them to refer back to earlier exercises if stuck.
6. **Use the self-check cell regularly**: After every 2-3 exercises, have students run the checker to catch errors early.

## Extension ideas
- Challenge students to calculate cube roots (`n ** (1/3)`)
- Explore what happens with negative exponents (`2 ** -2`)
- Investigate floating-point precision with very large powers
