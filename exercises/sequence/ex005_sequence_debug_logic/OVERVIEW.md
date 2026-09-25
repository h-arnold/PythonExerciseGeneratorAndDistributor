# Pedagogical Overview: ex005 Sequence Debug Logic

## Purpose

This exercise teaches students to identify and fix **logical errors** in sequential programs. Unlike syntax errors (which prevent code from running), logical errors allow code to execute but produce incorrect results. This distinction is crucial for developing debugging skills.

## Prerequisites

Students should already be familiar with:
- Basic `print()` and `input()` statements
- Variables and assignment
- Basic arithmetic operators (+, -, *, /)
- String concatenation with +

**Constructs NOT yet taught**: selection (if/elif/else), loops, lists, functions, imports, type conversion (int, float, str), f-strings, etc.

Each tagged solution must stay straight-line: simple assignments followed by one final `print()` payload. Use the scratch cells for experiments; prints from those untagged cells are not graded.

## Learning Objectives

By completing this exercise, students will:
1. Distinguish between syntax errors and logical errors
2. Read expected output and compare it to actual output
3. Trace through code to identify where logic goes wrong
4. Understand common logical mistakes beginners make
5. Develop systematic debugging strategies

## Common Student Misconceptions

### Exercise 1-3: Operator Confusion
- **Misconception**: Students may think Python can "guess" the right operator from variable names or context
- **Reality**: Python requires explicit, correct operators for each operation
- **Teaching tip**: Emphasise that `price + quantity` literally means "add", not "calculate total cost"

### Exercise 4, 8: String Concatenation
- **Misconception**: Python automatically adds spaces between concatenated strings
- **Reality**: String concatenation is literal - spaces must be explicitly included
- **Teaching tip**: Show that `"Hello" + "World"` produces `"HelloWorld"`, not `"Hello World"`

### Exercise 5, 10: Missing Spaces in Concatenation
- **Misconception**: Python adds spaces automatically when concatenating strings
- **Reality**: String concatenation is literal - you must explicitly add spaces
- **Teaching tip**: Show that `first_name + last_name` produces names run together without a space

### Exercise 2: Variable Names
- **Misconception**: Python will choose the "right" variable based on the expected output
- **Reality**: Python prints exactly the variable name written in the `print()` call
- **Teaching tip**: Trace each variable's assigned value before deciding what to print

### Exercise 6: Subtraction Order and Equivalence
- **Misconception**: The only correct expression is a subtraction written in one particular direction
- **Reality**: `paid - cost`, `abs(cost - paid)`, and `abs(paid - cost)` are equivalent for the expected value; the printed variable must still be `change`
- **Teaching tip**: Ask students to compare the value produced with the expected output, then justify whichever equivalent expression they used

### Exercise 9: Perimeter Formula
- **Misconception**: The perimeter must be written by listing each side separately
- **Reality**: `length + length + width + width`, `2 * length + 2 * width`, and `2 * (length + width)` are equivalent; count sides, not text occurrences
- **Teaching tip**: Let students write the formula in their preferred form and substitute the sample values to check it

### Exercise 7: Formula Complexity
- **Misconception**: Multiple operator errors can compound and confuse students
- **Reality**: Each operation must be correct individually
- **Teaching tip**: Use the untagged scratch cell to inspect intermediate values; keep the tagged cell to one final `print()` so the grader sees the required straight-line solution

## Difficulty Progression

- **Exercises 1-5**: Single error, easy to identify
  - Ex1: Wrong operator (+ vs *)
  - Ex2: Wrong variable name
  - Ex3: Wrong operator (/ vs *)
  - Ex4: Missing space in concatenation
  - Ex5: Missing space in name concatenation

- **Exercises 6-9**: Multiple errors, requiring careful analysis
  - Ex6: Wrong subtraction order + wrong print variable (2 bugs); `abs(cost - paid)` and `abs(paid - cost)` are also valid corrections
  - Ex7: Wrong operators in formula (2 bugs)
  - Ex8: Multiple missing spaces (conceptually 1 bug but 3 fixes)
  - Ex9: Incomplete formula + wrong print variable (2 bugs); any algebraically equivalent perimeter expression is valid
- **Exercise 10**: One missing space in the message concatenation

## Suggested Teaching Approach

### Before Starting
1. **Demonstrate the difference** between syntax errors (code won't run) and logical errors (code runs but gives wrong results)
2. **Model the debugging process**: Read expected output → run code → compare actual vs expected → identify the difference → trace back to find the cause
3. **Emphasise systematic thinking**: Don't just guess - understand *why* the output is wrong

### During the Exercise
1. **Let students struggle productively** - don't immediately point out the bugs
2. **Encourage explanation**: The explanation cells are crucial for cementing understanding
3. **Use pair programming**: Have students explain their thinking to a partner
4. **Highlight patterns**: After exercises 1-3, ask "What kinds of errors have we seen so far?"

### Worked Example (Exercise 1)
Walk through this as a class before students start:

```
Expected: 50
Code: total = price + quantity (where price=10, quantity=5)
Actual output: 15
Analysis: 10 + 5 = 15, but we need 10 × 5 = 50
Conclusion: Should use * (multiply) not + (add)
```

### Common Sticking Points

**Exercise 5 (name concatenation)**
- Many students struggle to understand why `first_name + last_name` produces `"AliceSmith"`
- **Demo tip**: Show in interactive Python: `print("Alice" + " " + "Smith")` and compare it with `print("Alice" + "Smith")`

**Exercise 7 (multiple operator errors)**
- Students may fix one error and miss the other
- **Teaching tip**: Encourage testing after each fix - if it's still wrong, there's another bug!

**Exercise 10 (spacing in a longer message)**
- A long message can contain several separate places where a space is needed
- **Teaching tip**: Ask students to read the expected output character by character and locate the boundary between `live in` and the city

## Extension Activities

For students who finish early:
1. **Create your own bug**: Write a working program, then introduce a logical error for a classmate to find
2. **Multiple solutions**: Exercise 6 accepts `paid - cost`, `abs(cost - paid)`, or `abs(paid - cost)`; Exercise 9 accepts equivalent perimeter forms
3. **Explain to the class**: Have students present one bug they found and how they fixed it

## Assessment Notes

Tests verify:
1. **Corrected code** produces the expected output, including multiple input cases for Exercises 5 and 10
2. **Straight-line live data flow** uses the original scenario values and the taught `+` concatenation rather than a decoy or hard-coded result
3. **Explanation cells** contain meaningful content of at least 50 characters
4. Only tagged exercise cells are graded; scratch-cell output is ignored

The explanation cells are crucial for formative assessment - they reveal whether students truly understand the bug or just guessed the fix.

## Estimated Time

- **Fast learners**: 20-30 minutes
- **Average students**: 40-50 minutes
- **Struggling students**: 60+ minutes (may need additional support on exercises 7-10)

## Links to Teaching Order

This exercise should follow:
- Syntax debugging exercises (ex004)
- Basic sequence introduction exercises

This exercise should precede:
- Selection (if/elif/else) constructs
- More complex debugging with multiple constructs
