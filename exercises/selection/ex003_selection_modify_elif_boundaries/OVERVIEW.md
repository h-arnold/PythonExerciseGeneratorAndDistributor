# Teaching Notes: Selection Modify — Elif Chains, Boundaries and Constants

## Prerequisites
- **Sequence construct**: `input()`, `int()` casting, `print()`, and arithmetic (`+`, `-`, `*`, `/`, `//`, `%`, `**`, `round()`).
- **Selection basics** (ideally `ex001_selection_modify_basics`): `if` and `if`-`else` with `==`, `!=`, `<`, `>`.
- This set introduces `<=`, `>=`, and the habit of using **constants**.

## Common Misconceptions
- **"Constants in Python are locked."** They are not — `UPPER_CASE` is a convention/promise, not enforcement. Make this explicit so students are not surprised they *can* still reassign.
- **Forgetting the threshold is now a name, not a number** — e.g. writing `if total >= FREE_DELIVERY_THRESHOLD` but leaving a stray `50` somewhere, or comparing against the wrong constant in an `elif`.
- **Boundary off-by-one confusion** — students may pick `<` instead of `<=` (or `>` instead of `>=`) and flip a band. Drill that `<=` / `>=` *include* the boundary value.
- **Editing only the `if` and forgetting the `elif`/`else` messages** when the task asks to change output.
- **Magic-number drift** — after refactoring, a threshold sometimes remains as a literal in one branch. Encourage replacing *every* occurrence.

## Teaching Approach
1. **Introduce constants first** with the linked [Introduction to Constants](../additional-resources/constants-intro.md); show that `FREE_DELIVERY_THRESHOLD = 50` reads better than a bare `50`.
2. **Exercises 1–3 are refactors only** — stress that behaviour must not change; the win is readability and one-place editing.
3. **From exercise 4**, keep the constant habit and now change values/operators. Walk through one example: "Change `PASS_MARK` from `60` to `40` — only the number at the top moves."
4. **For `elif` chains**, remind students the branches are checked top to bottom and the first true branch wins.
5. **One action per line** is modelled throughout — keep reads, casts, maths, constant assignment, and prints on separate lines.

## Worked Example (exercise 10 style)
```python
base = int(input("Enter base price: "))
qty = int(input("Enter quantity: "))
cost = base * qty
delivery = cost // 10          # floor division for a whole-pound fee
cost = cost + delivery
BULK_ORDER = 250               # constant, easy to tweak
if cost <= 20:
    print(f"Small order, cost £{cost}")
elif cost <= 50:
    print(f"Medium order, cost £{cost}")
elif cost <= 100:
    print(f"Large order, cost £{cost}")
elif cost <= BULK_ORDER:
    print(f"Bulk order, cost £{cost}")
else:
    print(f"Wholesale order, cost £{cost}")
```

## Differentiation
- **Stretch**: ask students to add a new `elif` band (e.g. a "wholesale" tier) using a new constant.
- **Support**: for exercises 1–3, give the exact constant names in the task (already done) so the focus stays on the refactor mechanics.
