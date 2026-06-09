# Python Arithmetic Cheatsheet

| Operator | Name | What it does | Example | Result |
|----------|------|-------------|---------|--------|
| `+` | Addition | Adds two numbers together | `5 + 3` | `8` |
| `-` | Subtraction | Subtracts one number from another | `10 - 4` | `6` |
| `*` | Multiplication | Multiplies two numbers | `6 * 7` | `42` |
| `/` | Division (float) | Divides and gives a decimal answer | `20 / 3` | `6.666...` |
| `//` | Floor division | Divides and **drops the decimal** — gives a whole number | `20 // 3` | `6` |
| `%` | Modulus (remainder) | Divides and gives the **remainder** left over | `20 % 3` | `2` |
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
| Round a decimal | `round(n, d)` | `round(6.666, 1) → 6.7` |
