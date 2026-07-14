# Introduction to Constants

## What is a constant?

A **constant** is a named value that stays the same while the program runs. Think of it like a label stuck to a fixed number or piece of text — once you decide what it is, you (and anyone else reading your code) promise not to change it.

This is different from a normal **variable**. A variable can change throughout the program (e.g. `score = 0` then later `score = score + 10`). A constant is meant to stay fixed, like a tax rate, a speed limit, or a qualifying score.

## How constants are used in Python

Python does **not** have a special keyword to lock a value as constant. Instead, programmers signal a constant by writing the name in **UPPER_CASE** with underscores between words:

```python
FREE_DELIVERY_THRESHOLD = 50
VAT_RATE = 0.20
MAX_LOGIN_ATTEMPTS = 3
```

You place constants near the top of your code, before any functions or logic, so they are easy to find.

The upper-case name is a **promise** to other programmers — and to your future self — that this value should not be reassigned later. You **can** still change it (Python will let you), but doing so would confuse anyone reading the code and goes against the convention.

## Why is it good practice?

- **No more "magic numbers"** — A number like `50` scattered through your code has no meaning on its own. `FREE_DELIVERY_THRESHOLD` explains itself.
- **Easier to read** — The name tells you what the value represents.
- **Easier to change** — Want to update the threshold? Change it in one place at the top, not in ten different spots.
- **Prevents accidents** — If a value should not change, naming it as a constant helps you avoid accidentally overwriting it later.

## Worked example

```python
FREE_DELIVERY_THRESHOLD = 50

total = int(input("Enter your total spend: "))

if total >= FREE_DELIVERY_THRESHOLD:
    print(f"Free delivery! Your total is £{total}")
else:
    print(f"You need £{FREE_DELIVERY_THRESHOLD - total} more for free delivery.")
```

**How it works:**

1. `FREE_DELIVERY_THRESHOLD` is set to `50` at the top — clear and easy to find.
2. The user enters their total, and the code converts it to an integer.
3. The `if` statement compares `total` against the constant. If the total meets or exceeds the threshold, the customer gets free delivery.
4. If the total is too low, the `else` branch tells them how much more they need — and it uses the constant again, so the message stays correct even if you change the threshold.
