# Teaching Notes: Selection Modify Basics (ex001)

## Prerequisites
- Students should know: variables, `print()`, `input()`, `int()` casting (for numeric input), basic arithmetic
- Previous construct: Sequence (exercises ex002–ex015)

## Common Misconceptions
- **`=` vs `==`**: Students often use a single `=` (assignment) in conditions instead of `==` (comparison). Point out this distinction early.
- **Forgetting the colon**: The `if` statement must end with `:`. Missing colons cause syntax errors.
- **Indentation**: The code inside the `if` block must be indented (4 spaces). Students may forget to indent or use inconsistent indentation.
- **`!=` looks strange**: The `!=` operator may look odd to beginners. Remind them it means "not equal to".
- **Input is a string**: When comparing numbers with `<` or `>`, students must remember to convert the input with `int()`. The starter code handles this, but reinforce why it's necessary.
- **Only one change needed**: For early exercises, students may overcomplicate and change more than needed. Remind them to read the task carefully — sometimes only the threshold number changes.

## Teaching Approach
1. Demonstrate the worked example from the notebook introduction first.
2. Let students work through exercises 1–5 independently, checking their understanding of the basic operators.
3. Pause after exercise 5 to reinforce the difference between `==` and `!=`.
4. Teach the `else` keyword using the "Introducing `else`" section. Demonstrate how `if-else` handles both true and false conditions.
5. Have students work through exercises 6–10, which build `if-else` logic progressively. Exercise 10 is the hardest, combining operator change, value change, and swapped branch messages.
6. Encourage students to run the code and observe the output before and after their changes.

## Exercise Guidance

| # | Topic | Key Learning Point |
|---|-------|-------------------|
| 1 | Favourite font (static) | Changing both the condition value and output message |
| 2 | Temperature threshold | Changing a `>` threshold number |
| 3 | Number guessing | Introducing `!=` (not equal to) |
| 4 | Age classification | Changing a `<` threshold with message |
| 5 | Maths quiz | Replacing `==` with `!=` |
| 6 | Score threshold (if-else) | Changing a `>` number and if-branch message |
| 7 | Name check (if-else) | Changing string comparison value and both messages |
| 8 | Height restriction (if-else) | Changing threshold and both messages |
| 9 | Drink order (if-else) | Changing string comparison and both messages |
| 10 | Password check (if-else) | Inverting logic (`==` → `!=`) with swapped branches |

## Worked Example (for teaching)
Display this on the board before students begin:

```python
# Original code
name = input("Enter your name: ")
if name == "Alice":
    print("Hello Alice!")
```

Ask: "How would we change this to print 'Goodbye Alice!' instead of 'Hello Alice!'?"
Answer: Only change the print message.

Then: "How would we change it to check for 'Bob' instead of 'Alice'?"
Answer: Change both the condition and the message.
