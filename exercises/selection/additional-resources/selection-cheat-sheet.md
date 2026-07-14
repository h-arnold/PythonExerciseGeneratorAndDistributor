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
| `<=`         | less than or equal to    | `5 <= 5`                 | `7 <= 5`                  |
| `>=`         | greater than or equal to | `5 >= 5`                 | `3 >= 5`                  |

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

### 7. The `if`-`elif`-`else` Statement Structure

Sometimes you need to check more than two possibilities. For example, you might want one message for high scores, a different message for medium scores, and another for low scores. The `elif` keyword (short for "else if") lets you add extra conditions after the first `if`.

```python
if condition1:
    # runs if condition1 is True
    print("First condition met")
elif condition2:
    # runs if condition1 was False but condition2 is True
    print("Second condition met")
elif condition3:
    # runs if condition1 and condition2 were False but condition3 is True
    print("Third condition met")
else:
    # runs if none of the above conditions were True
    print("Nothing matched")
```

Key rules:
- `elif` comes after an `if` block (or another `elif`), at the same indentation level as the `if`.
- You can have as many `elif` blocks as you need, though in practice keep your chains readable.
- The `else` block is optional but when included, it must always come last.
- Python checks conditions from top to bottom. The **first** condition that is True runs its block, and the rest are skipped.
- Only **one** block runs in the entire chain — never more.

> **⚠️ Important:** Order matters! Put the most specific or strictest condition first. For example, when checking grade boundaries, check the A grade threshold first, then B, then C:

```python
GRADE_A = 80
GRADE_B = 60
GRADE_C = 40
if score >= GRADE_A:
    print("Grade A")
elif score >= GRADE_B:
    print("Grade B")
elif score >= GRADE_C:
    print("Grade C")
else:
    print("Grade D")
```

If you reversed the order (checking `GRADE_C` first, then `GRADE_B`, then `GRADE_A`), the first condition (`score >= GRADE_C`) would always be True for scores that should be B or A grades, and the stricter checks would never run.

### 8. Worked Example — `elif`

**Program that categorises a parcel order using constants:**

```python
items = int(input("Enter number of items: "))
SMALL_LIMIT = 10
MEDIUM_LIMIT = 30
if items <= SMALL_LIMIT:
    print("Small order")
elif items <= MEDIUM_LIMIT:
    print("Medium order")
else:
    print("Large order")
```

**How it works:**
1. The program asks for the number of items and stores it in `items`.
2. Constants `SMALL_LIMIT` and `MEDIUM_LIMIT` are set to `10` and `30`.
3. The `if` checks whether `items <= SMALL_LIMIT`. If True, it prints "Small order" and skips the rest.
4. If the `if` condition is False (more than `SMALL_LIMIT`), Python moves to the `elif` and checks `items <= MEDIUM_LIMIT`.
5. If the `elif` is True (between 11 and 30 items), it prints "Medium order" and skips the `else`.
6. If both conditions are False (more than `MEDIUM_LIMIT`), the `else` block runs and prints "Large order".

**What happens with different inputs:**
- Input `5` → `items <= SMALL_LIMIT` is True → prints "Small order"
- Input `20` → `items <= SMALL_LIMIT` is False, then `items <= MEDIUM_LIMIT` is True → prints "Medium order"
- Input `50` → both conditions are False → prints "Large order"

### 9. Common Mistakes to Avoid

- **Using `=` instead of `==`:** Remember, `=` assigns a value, `==` checks equality.
- **Forgetting the colon (`:`):** Every `if` statement must end with a colon on the condition line.
- **Forgetting to indent:** The code inside the `if` block must be indented. Python will give an error otherwise.
- **Comparing different types:** Make sure you compare values of the same type (e.g., both strings or both numbers).
