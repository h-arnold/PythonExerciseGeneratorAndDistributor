"""Repository-only construct-helper checks for ex007."""

from __future__ import annotations

import ast

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex007_sequence_debug_casting"
construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
ex007 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _interactive_issues(code: str, exercise_no: int) -> list[str]:
    rules = ex007.EX007_INTERACTIVE_CONSTRUCTS[exercise_no]
    return construct_checks.interactive_construct_issues(
        ast.parse(code),
        expected_input_count=len(ex007.EX007_INPUT_CASES[exercise_no][0]["inputs"]),
        required_calls=rules.get("required_calls", ()),
        required_ops=rules.get("required_ops", ()),
        forbidden_ops=rules.get("forbidden_ops", ()),
    )


def _static_issues(code: str, exercise_no: int) -> list[str]:
    rules = ex007.EX007_STATIC_CONSTRUCTS[exercise_no]
    return construct_checks.static_construct_issues(
        ast.parse(code),
        required_calls=rules.get("required_calls", ()),
        required_ops=rules.get("required_ops", ()),
        forbidden_ops=rules.get("forbidden_ops", ()),
        relevant_names=rules.get("relevant_names", ()),
    )


def test_interactive_construct_issues_accept_output_chain_using_inputs() -> None:
    issues = _interactive_issues(
        """
price_text = input("Enter price per item (£): ")
quantity_text = input("Enter quantity: ")
price = float(price_text)
quantity = int(quantity_text)
total_cost = price * quantity
print("Total cost: £" + str(total_cost))
""",
        7,
    )
    assert issues == []


def test_interactive_construct_issues_accept_compact_input_cast() -> None:
    issues = _interactive_issues(
        """
age = int(input("Enter your age: "))
next_age = age + 1
print("Next year you will be " + str(next_age))
""",
        3,
    )
    assert issues == []


def test_interactive_construct_issues_accept_compact_repeat_and_float_casts() -> None:
    repeat_issues = _interactive_issues(
        """
word = input("Word to repeat: ")
repeat = int(input("How many times? "))
print(word * repeat)
""",
        5,
    )
    temperature_issues = _interactive_issues(
        """
temperature = float(input("Enter temperature in Celsius: "))
fahrenheit = temperature * 9 / 5 + 32
print("Temperature in Fahrenheit: " + str(fahrenheit))
""",
        6,
    )
    assert repeat_issues == []
    assert temperature_issues == []


def test_interactive_construct_issues_accept_top_level_aliases_and_tuple_input() -> None:
    alias_issues = _interactive_issues(
        """
age_text = input("Enter your age: ")
age = int(age_text)
next_age = age + 1
next_age_text = str(next_age)
print("Next year you will be " + next_age_text)
""",
        3,
    )
    tuple_issues = _interactive_issues(
        """
price, quantity = float(input("Enter price per item (£): ")), int(input("Enter quantity: "))
total = price * quantity
total_text = str(total)
print("Total cost: £", total_text)
""",
        7,
    )
    assert alias_issues == []
    assert tuple_issues == []


def test_interactive_construct_issues_accept_builtins_input() -> None:
    issues = _interactive_issues(
        """
age = int(builtins.input("Enter your age: "))
next_age = age + 1
print("Next year you will be " + str(next_age))
""",
        3,
    )
    assert issues == []


def test_interactive_construct_issues_reject_empty_string_cast_neutralization() -> None:
    issues = _interactive_issues(
        """
age = int(input("Enter your age: "))
next_age = age + 1
print("Next year you will be", next_age, str(''))
""",
        3,
    )
    assert any("cast" in issue.lower() for issue in issues)


def test_interactive_construct_issues_reject_boolean_neutralization() -> None:
    issues = _interactive_issues(
        """
age = int(input("Enter your age: "))
print("Next year you will be " + (age and ''))
""",
        3,
    )
    assert any("boolean" in issue.lower() for issue in issues)


def test_interactive_construct_issues_reject_boolop_compare_branch() -> None:
    issues = _interactive_issues(
        """
price_text = input("Enter price per item (£): ")
quantity_text = input("Enter quantity: ")
price = float(price_text)
quantity = int(quantity_text)
result = "6.0" if price_text == "1.5" and quantity_text == "4" else "10.0"
print("Total cost: £" + str(result))
""",
        7,
    )
    assert issues


def test_interactive_construct_issues_reject_add_only_in_output_label() -> None:
    issues = _interactive_issues(
        """
age = int(input("Enter your age: "))
print("Next year you will be " + str(age))
""",
        3,
    )
    assert any("operator" in issue.lower() for issue in issues)


def test_interactive_construct_issues_reject_unrelated_cast_operand() -> None:
    issues = _interactive_issues(
        """
age = int(input("Enter your age: "))
next_age = age + 1
print("Next year you will be", next_age, str(''))
""",
        3,
    )
    assert any("cast" in issue.lower() for issue in issues)


def test_interactive_construct_issues_reject_numeric_cast_of_literal() -> None:
    issues = _interactive_issues(
        """
age_text = input("Enter your age: ")
age = int(0)
next_age = age + 1
print("Next year you will be", next_age, age_text)
""",
        3,
    )
    assert issues


def test_interactive_construct_issues_reject_operation_outside_final_output() -> None:
    issues = _interactive_issues(
        """
price_text = input("Enter price per item (£): ")
quantity_text = input("Enter quantity: ")
price = float(price_text)
quantity = int(quantity_text)
unused_total = price * quantity
print("Total cost: £6.0")
""",
        7,
    )
    assert any("relevant task values" in issue for issue in issues)


def test_interactive_construct_issues_reject_lookup_table_output() -> None:
    issues = _interactive_issues(
        """
price_text = input("Enter price per item (£): ")
quantity_text = input("Enter quantity: ")
price = float(price_text)
quantity = int(quantity_text)
lookup = {("1.5", "4"): "6.0", ("2.5", "4"): "10.0"}
result = lookup[(price, quantity)]
print("Total cost: £" + str(result))
""",
        7,
    )
    assert issues


def test_interactive_construct_issues_reject_conditional_data_flow() -> None:
    issues = _interactive_issues(
        """
price_text = input("Enter price per item (£): ")
quantity_text = input("Enter quantity: ")
price = float(price_text)
quantity = int(quantity_text)
if price_text == "1.5" and quantity_text == "4":
    result = "6.0"
else:
    result = "10.0"
print("Total cost: £" + str(result))
""",
        7,
    )
    assert any("straight-line" in issue or "condition" in issue for issue in issues)


def test_interactive_construct_issues_reject_floor_division_output_chain() -> None:
    issues = _interactive_issues(
        """
total_bill_text = input("Total bill (£): ")
people_text = input("Number of people: ")
total_bill = float(total_bill_text)
people = int(people_text)
tip_rate = 0.1
total_with_tip = total_bill + total_bill * tip_rate
per_person = total_with_tip // people
print("Each person pays: £" + str(per_person))
""",
        10,
    )
    assert any("/" in issue for issue in issues)
    assert any("//" in issue for issue in issues)


@pytest.mark.parametrize(
    "code",
    [
        """
age = int(input("Enter your age: "))
if age:
    next_age = age + 1
else:
    next_age = 0
print("Next year you will be " + str(next_age))
""",
        """
age = int(input("Enter your age: "))
next_age = age + 1 if age else 0
print("Next year you will be " + str(next_age))
""",
        """
age = int(input("Enter your age: "))
for _ in range(1):
    next_age = age + 1
print("Next year you will be " + str(next_age))
""",
        """
age = int(input("Enter your age: "))
while age > 0:
    next_age = age + 1
print("Next year you will be " + str(next_age))
""",
        """
def solve():
    age = int(input("Enter your age: "))
    return age + 1
print("Next year you will be " + str(solve()))
""",
        """
class Helper:
    pass
age = int(input("Enter your age: "))
print("Next year you will be " + str(age + 1))
""",
        """
import math
age = int(input("Enter your age: "))
print("Next year you will be " + str(age + 1))
""",
        """
age = int(input("Enter your age: "))
age += 1
print("Next year you will be " + str(age))
""",
        """
age = int(input("Enter your age: "))
print("Next year you will be " + str((next_age := age + 1)))
""",
        """
age = int(input("Enter your age: "))
values = [age + 1]
print("Next year you will be " + str(values[0]))
""",
        """
age = int(input("Enter your age: "))
print("Next year you will be " + str(age).strip())
""",
        """
int = 3
age = input("Enter your age: ")
print("Next year you will be " + str(age))
""",
    ],
)
def test_interactive_construct_issues_reject_unsupported_side_effects(code: str) -> None:
    assert _interactive_issues(code, 3)


def test_static_construct_issues_reject_dead_cast() -> None:
    issues = _static_issues(
        """
count = 3
unused_text = str(count)
print("You have 3 pens")
""",
        1,
    )
    assert issues


def test_static_construct_issues_reject_dead_division() -> None:
    issues = _static_issues(
        """
total_distance = 7
days = 2
unused_average = total_distance / days
print("Average per day: 3.5 km")
""",
        4,
    )
    assert issues


def test_static_construct_issues_reject_empty_string_cast() -> None:
    issues = _static_issues(
        """
count = 3
print("You have", count, str(''))
""",
        1,
    )
    assert any("cast" in issue.lower() for issue in issues)
