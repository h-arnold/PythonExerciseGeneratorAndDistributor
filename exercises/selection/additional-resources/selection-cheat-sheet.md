# Selection (If Statements) Cheat Sheet

### 1. What is Selection?

Selection allows a program to make decisions. It checks a **condition** and runs certain code only when that condition is **true**.

Think of it like a gate: if the condition is true, the gate opens and the code runs. If the condition is false, the gate stays closed.

### 2. The `if` Statement Structure

```python
if condition:
    # this code runs only if the condition is True
    print("Something happens!")
```

Key rules:
- The `if` keyword starts the statement.
- The **condition** comes after `if` and ends with a colon (`:`).
- The code that runs when the condition is true must be **indented** (4 spaces is standard).
- Only the indented code is controlled by the condition — code at the same level as the `if` runs regardless.

### 3. Comparison Operators

These operators are used to build conditions by comparing values:

| **Operator** | **Meaning**         | **Example that is True** | **Example that is False** |
|:-------------|:--------------------|:-------------------------|:--------------------------|
| `==`         | equal to            | `5 == 5`                 | `5 == 3`                  |
| `!=`         | not equal to        | `5 != 3`                 | `5 != 5`                  |
| `<`          | less than           | `3 < 5`                  | `5 < 3`                   |
| `>`          | greater than        | `5 > 3`                  | `3 > 5`                   |

**Important:** `==` is used for comparison (is it equal?), while `=` is used for assignment (giving a variable a value).

### 4. Worked Example

**Program that checks a favourite colour:**

```python
colour = input("What is your favourite colour? ")
if colour == "blue":
    print("Blue is a nice colour!")
```

**How it works:**
1. The program asks the user to type their favourite colour and stores it in the variable `colour`.
2. The `if` statement checks whether `colour` is equal to `"blue"`.
3. If the user typed `"blue"`, the condition is **true** and `"Blue is a nice colour!"` is printed.
4. If the user typed anything else, the condition is **false** and nothing is printed.

**Task:** Change the program so it says `"Blue is the best!"` when the user types `"blue"`.

**Solution:** Change the `print` message:

```python
colour = input("What is your favourite colour? ")
if colour == "blue":
    print("Blue is the best!")
```

**Expected output** (when the user types `blue`):
```
Blue is the best!
```

### 5. The `if`-`else` Statement Structure

Sometimes you want to do one thing when the condition is **true** and a **different** thing when it is **false**. The `else` keyword adds a second block that runs only when the condition is false.

```python
if condition:
    # this code runs if the condition is True
    print("Condition was true!")
else:
    # this code runs if the condition is False
    print("Condition was false!")
```

Key rules:
- `else` comes **after** the `if` block, at the same indentation level as the `if`.
- The `else` line also ends with a colon (`:`).
- Only **one** of the two blocks will run — never both.

### 6. Worked Example — `if-else`

**Program that checks if someone likes cats:**

```python
animal = input("What is your favourite animal? ")
if animal == "duck":
    print("Quack! Ducks are the best!")
else:
    print("No one's perfect I guess...")
```

**How it works:**
1. The program asks the user to type their favourite animal and stores it in `animal`.
2. The `if` checks whether `animal` is equal to `"duck"`.
3. If the user typed `"duck"`, the condition is **true** and `"Quack! Ducks are the best!"` is printed.
4. If the user typed anything else, the condition is **false** and `"No one's perfect I guess..."` is printed instead.

### 6. Common Mistakes to Avoid

- **Using `=` instead of `==`:** Remember, `=` assigns a value, `==` checks equality.
- **Forgetting the colon (`:`):** Every `if` statement must end with a colon on the condition line.
- **Forgetting to indent:** The code inside the `if` block must be indented. Python will give an error otherwise.
- **Comparing different types:** Make sure you compare values of the same type (e.g., both strings or both numbers).
