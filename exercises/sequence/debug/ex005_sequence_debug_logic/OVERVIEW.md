# Pedagogical Overview: ex005 Sequence Debug Logic

## Purpose

This exercise teaches students to identify and fix **logical errors** in sequential programs. Unlike syntax errors (which prevent code from running), logical errors allow code to execute but produce incorrect results. This distinction is crucial for developing debugging skills.

## Prerequisites

Students should already be familiar with:
- Basic `print()` and `input()` statements
- Variables and assignment
- Basic arithmetic operators (+, -, *, /)
- String concatenation with +

**Constructs NOT yet taught**: selection (if/elif/else), loops, lists, functions, type conversion (int, float, str), etc.

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

### Exercise 6, 9: Variable Mix-ups
- **Misconception**: Python will use the "right" variable based on context
- **Reality**: Python uses exactly the variable name you write
- **Teaching tip**: Stress the importance of double-checking variable names, especially after copy-paste

### Exercise 7: Formula Complexity
- **Misconception**: Multiple operator errors can compound and confuse students
- **Reality**: Each operation must be correct individually
- **Teaching tip**: Encourage students to test intermediate values (e.g., print `total` before calculating `average`)

## Difficulty Progression

- **Exercises 1-5**: Single error, easy to identify
  - Ex1: Wrong operator (+ vs *)
  - Ex2: Wrong variable name
  - Ex3: Wrong operator (/ vs *)
  - Ex4: Missing space in concatenation
  - Ex5: Missing space in name concatenation

- **Exercises 6-10**: Multiple errors, requires careful analysis
  - Ex6: Wrong subtraction order + wrong print variable (2 bugs)
  - Ex7: Wrong operators in formula (2 bugs)
  - Ex8: Multiple missing spaces (conceptually 1 bug but 3 fixes)
  - Ex9: Incomplete formula + wrong print variable (2 bugs)
  - Ex10: Missing space in message concatenation

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

**Exercise 5 (input conversion)**
- Many students struggle to understand why `"7" + "3"` = `"73"`
- **Demo tip**: Show in interactive Python: `type(input("Enter a number: "))` returns `<class 'str'>`

**Exercise 7 (multiple operator errors)**
- Students may fix one error and miss the other
- **Teaching tip**: Encourage testing after each fix - if it's still wrong, there's another bug!

**Exercise 10 (complex formula)**
- The temperature conversion formula is mathematically complex for some students
- **Teaching tip**: Provide the correct formula (F = C × 9/5 + 32) and focus debugging on the conversion issue, not deriving the formula

## Extension Activities

For students who finish early:
1. **Create your own bug**: Write a working program, then introduce a logical error for a classmate to find
2. **Multiple solutions**: Some exercises can be fixed in different ways (e.g., Exercise 6 could swap the operands OR use absolute value)
3. **Explain to the class**: Have students present one bug they found and how they fixed it

## Assessment Notes

Tests verify:
1. **Corrected code** produces the expected output
2. **Explanation cells** contain meaningful content (more than 10 characters)

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
