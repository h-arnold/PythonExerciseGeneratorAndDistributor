# Python Arithmetic Cheatsheet

| Operator | Name | What it does | Example | Result |
|----------|------|-------------|---------|--------|
| `+` | Addition | Adds two numbers together | `5 + 3` | `8` |
| `-` | Subtraction | Subtracts one number from another | `10 - 4` | `6` |
| `*` | Multiplication | Multiplies two numbers | `6 * 7` | `42` |
| `/` | Division (float) | Divides and gives a decimal answer | `20 / 3` | `6.666...` |
| `//` | Floor division | Divides and **drops the decimal** — gives a whole number | `20 // 3` | `6` |
| `%` | Modulus (remainder) | Divides and gives the **remainder** left over | `20 % 3` | `2` |
| `**` | Exponentiation (power) | Raises a number to the power of another | `2 ** 10` | `1024` |
| `int()` | Integer conversion | Converts a value to a whole number (truncates decimals) | `int(3.77)` | `3` |
| `float()` | Float conversion | Converts a value to a decimal number | `float("5.5")` | `5.5` |
| `round()` | Rounding | Rounds a number to a set number of decimal places | `round(6.666, 1)` | `6.7` |

---

## Worked examples

### `+` Addition — add numbers together

```python
pocket_money = 5
birthday_money = 20
total = pocket_money + birthday_money
print(total)    # 25
```

> `+` adds the two amounts together to find the total.

---

### `-` Subtraction — find the difference

```python
total_books = 15
given_away = 4
remaining = total_books - given_away
print(remaining)    # 11
```

> `-` takes away `given_away` from `total_books` to find what's left.

---

### `*` Multiplication — repeated addition

```python
ticket_price = 8
friends = 4
total_cost = ticket_price * friends
print(total_cost)    # 32
```

> `*` multiplies the price by the number of friends to find the total cost.

---

### `/` Division — split into equal parts (decimal answer)

```python
total_pizza_slices = 10
people = 3
slices_per_person = total_pizza_slices / people
print(slices_per_person)    # 3.333...
```

> `/` divides 10 slices among 3 people — each person gets **3.333...** slices (a decimal).

---

### `//` Floor division — split into whole groups only

```python
students = 29
group_size = 4
full_groups = students // group_size
print(full_groups)    # 7
```

> `//` divides but **drops the remainder**. 29 students in groups of 4 makes **7 full groups** — the leftover 1 student doesn't count as a group.

---

### `%` Modulus — find what's left over

```python
cupcakes = 29
per_box = 4
leftover = cupcakes % per_box
print(leftover)    # 1
```

> `%` (modulus) gives the **remainder** after making full groups. 29 cupcakes with 4 per box leaves **1 cupcake** leftover.

---

### `//` and `%` — a perfect pair

Use `//` to find **how many whole groups**, and `%` to find **what's left over**.

```python
minutes = 125
hours = minutes // 60      # 2 full hours
mins_left = minutes % 60   # 5 leftover minutes

print(f"{minutes} minutes is {hours} hours and {mins_left} minutes")
# 125 minutes is 2 hours and 5 minutes
```

```python
pence = 389
pounds = pence // 100      # 3 whole pounds
leftover_pence = pence % 100   # 89 leftover pence

print(f"{pence}p is £{pounds} and {leftover_pence}p")
# 389p is £3 and 89p
```

---

### `**` Exponentiation — raise to a power

The `**` operator raises a number (the **base**) to the power of another number (the **exponent**).

```python
base = 3
exponent = 4
result = base ** exponent
print(result)    # 81
```

> `3 ** 4` means 3 × 3 × 3 × 3 = 81.

---

#### Square a number (`** 2`)

```python
number = 8
square = number ** 2
print(square)    # 64
```

> `8 ** 2` is the same as `8 * 8`.

---

#### Cube a number (`** 3`)

```python
number = 6
cube = number ** 3
print(cube)    # 216
```

> `6 ** 3` is the same as `6 * 6 * 6`.

---

#### Square root (`** 0.5`)

Raising to the power of `0.5` gives the square root.

```python
number = 144
root = number ** 0.5
print(root)    # 12.0
```

> `144 ** 0.5` is the square root of 144. The result is a float (`12.0`), even when the answer is a whole number.

---

#### Area of a circle (`pi * radius ** 2`)

```python
pi = 3.14159
radius = 5
area = pi * radius ** 2
print(area)    # 78.53975
```

> `radius ** 2` squares the radius, then `pi *` multiplies by π to get the area.

> **Order of operations**: `**` is calculated before `*`, so `pi * radius ** 2` works correctly without parentheses.

---

### `int()` — convert to a whole number

When you read input with `input()`, the result is always text (a string). Use `int()` to turn it into a whole number before doing maths.

```python
age_input = input("Enter your age: ")
age = int(age_input)
next_year = age + 1
print(f"Next year you will be {next_year}")
```

> Without `int()`, `age_input + 1` would fail because you can't add a number to text.

Store the input and conversion in **separate steps** to keep each step clear:

```python
number_input = input("Enter a number: ")   # Step 1: read the text
number_int = int(number_input)             # Step 2: convert to integer
```

---

### `float()` — convert to a decimal number

Use `float()` when your number might have a decimal point (e.g. lengths, weights, money).

```python
side_input = input("Enter the side length: ")
side_float = float(side_input)
area = side_float ** 2
print(area)
```

> `float("9")` gives `9.0` — it works with whole numbers too, but always produces a decimal.

---

### `round()` — tidy up decimal answers

```python
total_points = 20
games = 3
average = total_points / games          # 6.666...
average = round(average, 1)             # 6.7
print(average)
```

> `round(number, decimal_places)` rounds a long decimal to something neat.

Rounding to **2 decimal places** is useful for money:

```python
total = round(3.771, 2)
print(total)    # 3.77
```

---

## Quick summary

| You want to… | Use | Example |
|---|---|---|
| Add | `+` | `5 + 3 → 8` |
| Subtract | `-` | `10 - 4 → 6` |
| Multiply | `*` | `6 * 7 → 42` |
| Divide (decimal) | `/` | `20 / 3 → 6.666` |
| Divide (whole numbers only) | `//` | `20 // 3 → 6` |
| Find the remainder | `%` | `20 % 3 → 2` |
| Raise to a power | `**` | `2 ** 10 → 1024` |
| Square a number | `** 2` | `8 ** 2 → 64` |
| Cube a number | `** 3` | `6 ** 3 → 216` |
| Square root | `** 0.5` | `144 ** 0.5 → 12.0` |
| Convert text to integer | `int(text)` | `int("8") → 8` |
| Convert text to float | `float(text)` | `float("5.5") → 5.5` |
| Round a decimal | `round(n, d)` | `round(6.666, 1) → 6.7` |
