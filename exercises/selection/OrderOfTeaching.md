# Order of teaching — Selection

These exercises are intended to be taught in the following order:

1. [**Selection Modify Basics**](./ex001_selection_modify_basics/)

[Supporting docs](./ex001_selection_modify_basics/)
[Notebook](./ex001_selection_modify_basics/notebooks/student.ipynb)

- Focus: Simple `if` statements (exercises 1–5) and `if-else` logic (exercises 6–10) with `==`, `!=`, `<`, and `>` comparison operators. Students modify working programs by changing the condition value, comparison operator, threshold number, or output message.
- Type: Modification exercises (10 parts) where students change existing working code to meet new requirements.
- Purpose: Introduce selection as a way to make decisions in code. Students learn how changing a condition or message affects program behaviour without the complexity of writing from scratch.
- Comparison operators covered: `==` (ex1, ex7, ex9), `!=` (ex3, ex5, ex10), `<` (ex4), `>` (ex2, ex6, ex8)

3. [**Selection Modify: Elif Chains, Boundaries and Constants**](./ex003_selection_modify_elif_boundaries/)

[Supporting docs](./ex003_selection_modify_elif_boundaries/)
[Notebook](./ex003_selection_modify_elif_boundaries/notebooks/student.ipynb)
[Constants intro](./additional-resources/constants-intro.md)

- Focus: Introduces the boundary operators `<=` and `>=` and the habit of storing fixed values in UPPER_CASE **constants**, then modifying `if`/`elif`/`else` chains (including multi-`elif` chains) so students change constant values, operators, and messages. All output uses f-strings; arithmetic (`+`, `*`, `//`, `%`, `round()`) is used inside conditions.
- Type: Modification exercises (10 parts). Exercises 1–3 are pure refactors (extract literals into constants, behaviour unchanged); exercises 4–10 keep the constant habit and require changing the constant value and/or operator as difficulty rises. `elif` chains grow from one `elif` (ex6–7) to two (ex8), three (ex9), and a multi-branch chain that also changes the cost formula (ex10).
- Purpose: Extend selection beyond `==`/`!=`/`<`/`>` and build good practice around named constants before students meet functions. Builds directly on `ex001`.
- Prerequisite reading: [Introduction to Constants](./additional-resources/constants-intro.md)

2. [**Selection Debug If Then Else**](./ex002_selection_debug_if_then_else/)

[Supporting docs](./ex002_selection_debug_if_then_else/)
[Notebook](./ex002_selection_debug_if_then_else/notebooks/student.ipynb)

- Focus: Debugging syntax errors, logic errors, and mixed errors in `if-else` statements. Exercises cover missing colons, wrong operators (`=` vs `==`/`>=`/`>`), missing indentation, unquoted strings, swapped branches, off-by-one comparisons, missing `else` clauses, and wrong variable names.
- Type: Debug exercise (20 parts) with graduated difficulty: 1 error → 5 errors per exercise.
- Purpose: Build debugging skills by having students identify and fix common beginner mistakes in selection statements.
