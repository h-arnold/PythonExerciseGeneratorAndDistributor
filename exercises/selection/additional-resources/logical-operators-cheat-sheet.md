# Logical Operators (AND, OR, NOT) Cheat Sheet

### 1. What Are Logical Operators?

A comparison such as `age >= 11` asks one true-or-false question. Logical operators join two or more of these questions into a bigger condition:

- `and` — every joined question must be true.
- `or` — at least one joined question must be true.
- `not` — flips a question around (true becomes false, false becomes true).

Think of them as joining gates: `and` is a gate that only opens when **both** guards agree, `or` opens when **either** guard agrees, and `not` swaps the sign on the door.

### 2. The `and` Operator

```python
if age >= 11 and age <= 16:
    print("You can join the club!")
```

The whole condition is true only when **both** sides are true:

| `age >= 11` | `age <= 16` | `age >= 11 and age <= 16` |
|:------------|:------------|:--------------------------|
| True        | True        | **True**                  |
| True        | False       | **False**                 |
| False       | True        | **False**                 |
| False       | False       | **False**                 |

**What happens with different values:**
- Age `14` → both sides true → prints "You can join the club!"
- Age `20` → second side false → nothing is printed
- Age `8` → first side false → nothing is printed

### 3. The `or` Operator

```python
if day == "Saturday" or day == "Sunday":
    print("Lie-in day!")
```

The whole condition is true when **at least one** side is true (both being true also counts):

| `day == "Saturday"` | `day == "Sunday"` | Combined with `or` |
|:--------------------|:------------------|:-------------------|
| True                | True              | **True**           |
| True                | False             | **True**           |
| False               | True              | **True**           |
| False               | False             | **False**          |

**What happens with different values:**
- Day `"Sunday"` → second side true → prints "Lie-in day!"
- Day `"Saturday"` → first side true → prints "Lie-in day!"
- Day `"Monday"` → both sides false → nothing is printed

### 4. The `not` Operator

`not` reverses a single question. It goes **before** the question it flips, and brackets keep it readable:

```python
if not (score >= 50):
    print("Not a pass yet")
else:
    print("A pass!")
```

| `score` | `score >= 50` | `not (score >= 50)` |
|:--------|:--------------|:--------------------|
| 30      | False         | **True**            |
| 50      | True          | **False**           |
| 72      | True          | **False**           |

Key rules:
- The behaviour is identical to writing the check the other way round (`score < 50` here) — only the wording changes.
- Always put brackets around the question being flipped: `not (age < 5)` is much easier to read than `not age < 5`.

### 5. Worked Example — `and`

**Program that checks both ends of an age range:**

```python
age_input = input("Enter your age: ")
age = int(age_input)
if age >= 11 and age <= 16:
    print(f"In range: age {age} fits the club")
else:
    print(f"Out of range: age {age} does not fit")
```

**How it works:**
1. The program asks for the age, converts it to an integer, and stores it in `age`.
2. The `if` asks two questions at once: is `age` 11 or older, **and** is `age` 16 or younger?
3. If the user types `14`, both questions are true, so `"In range: age 14 fits the club"` is printed.
4. If the user types `20`, the second question is false, so the whole `and` is false and `"Out of range: age 20 does not fit"` is printed instead.

**Task:** Change the program so the club accepts ages 10 to 18 instead.

**Solution:** Change both boundary numbers:

```python
age_input = input("Enter your age: ")
age = int(age_input)
if age >= 10 and age <= 18:
    print(f"In range: age {age} fits the club")
else:
    print(f"Out of range: age {age} does not fit")
```

**Expected output** (when the user types `20`):
```
Enter your age: 20
Out of range: age 20 does not fit
```

### 6. Worked Example — `or`

**Program that spots weekend days:**

```python
day = input("Enter the day: ")
if day == "Saturday" or day == "Sunday":
    print(f"Weekend! {day} is a lie-in day")
else:
    print(f"School day. {day} needs an early start")
```

**How it works:**
1. The program asks for the day and stores it in `day`.
2. The `if` asks whether `day` is Saturday **or** Sunday — either answer counts.
3. If the user types `"Sunday"`, the second question is true, so `"Weekend! Sunday is a lie-in day"` is printed.
4. If the user types `"Monday"`, both questions are false, so `"School day. Monday needs an early start"` is printed instead.

### 7. Worked Example — `and` with `not`

**Program for a film club that needs members old enough and comfortable in the dark:**

```python
age_input = input("Enter your age: ")
age = int(age_input)
scared = input("Are you scared of the dark? (yes/no): ")
AGE_LIMIT = 10
if age >= AGE_LIMIT and not (scared == "yes"):
    print(f"Come in! Age {age}, scared {scared}")
else:
    print(f"Maybe later. Age {age}, scared {scared}")
```

**How it works:**
1. The program reads the age (converting it to an integer) and the scared answer separately — one action per line.
2. The `if` needs two things together: old enough, **and** not scared.
3. Age `12` with `"no"` → old enough is true and `not (scared == "yes")` is true → `"Come in! Age 12, scared no"`.
4. Age `12` with `"yes"` → the `not` flips the scared answer to false → `"Maybe later. Age 12, scared yes"`.
5. Age `8` with `"no"` → the age question is false → `"Maybe later. Age 8, scared no"`.

### 8. Mixing `and` with `or` — Use Brackets

Sometimes you need a mixture: one thing **must** be true, plus **either** of two extras. Brackets group the either-or part so Python checks it first:

```python
member = input("Are you a member? (yes/no): ")
spend_input = input("Enter your spend: ")
spend = int(spend_input)
SPEND_LIMIT = 40
SENIOR_AGE = 60
age_input = input("Enter your age: ")
age = int(age_input)
if member == "yes" and (spend >= SPEND_LIMIT or age >= SENIOR_AGE):
    print(f"Discount for you! Spend £{spend}, age {age}")
else:
    print(f"Full price. Spend £{spend}, age {age}")
```

**How it works:**
1. The brackets are checked first: is the spend high enough, **or** is the visitor senior?
2. Then `and` combines that answer with membership: members **plus** one qualifying extra get the discount.
3. `yes`, `10`, `20` → member but neither extra → `"Full price. Spend £10, age 20"`.
4. `yes`, `50`, `20` → member with enough spend → `"Discount for you! Spend £50, age 20"`.
5. `no`, `50`, `70` → not a member, so the `and` fails straight away → `"Full price. Spend £50, age 70"`.

> **⚠️ Important:** Without brackets, `and` is checked before `or`, which can give the discount to the wrong people. Whenever you mix them, put the either-or part in brackets — the brackets mirror how you would say the rule out loud: "a member, and (big spender or senior)".

### 9. Common Mistakes to Avoid

- **Using `&`, `|` or `!` instead of `and`, `or`, `not`:** Those symbols belong to other languages (or mean something different in Python). Always use the words.
- **Forgetting brackets when mixing `and` with `or`:** `member == "yes" and spend >= 40 or age >= 60` is checked as `(member == "yes" and spend >= 40) or age >= 60`, which lets every senior in for free with no membership. Add the brackets to say what you mean.
- **Mixing up which word you need:** Read the rule out loud. "Both" and "as well as" mean `and`; "either" and "or" mean `or`. If reaching one target is enough for a pass, that is `or`, not `and`.
- **Writing `== True` or `== False`:** Comparisons already produce true-or-false answers, so `if member == "yes" == True:` is clutter. Just write `if member == "yes":`.
- **Comparing text without matching exactly:** `"Sunday"` with a capital S is not equal to `"sunday"`. String comparisons must match letter for letter, including capitals.
