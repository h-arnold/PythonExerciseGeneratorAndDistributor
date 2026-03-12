from __future__ import annotations

import ast

from tests.exercise_expectations import ex007_data_types_debug_casting as ex007
from tests.exercise_framework.ex007_construct_checks import interactive_construct_issues


def _construct_issues(code: str, exercise_no: int) -> list[str]:
    rules = ex007.EX007_INTERACTIVE_CONSTRUCTS[exercise_no]
    return interactive_construct_issues(
        ast.parse(code),
        expected_input_count=len(
            ex007.EX007_INPUT_CASES[exercise_no][0]["inputs"]),
        required_calls=rules.get("required_calls", ()),
        required_ops=rules.get("required_ops", ()),
        forbidden_ops=rules.get("forbidden_ops", ()),
    )


def test_interactive_construct_issues_accept_output_chain_using_inputs() -> None:
    issues = _construct_issues(
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


def test_interactive_construct_issues_reject_hardcoded_prints_with_decoy_calculation() -> None:
    issues = _construct_issues(
        """
price_text = input("Enter price per item (£): ")
quantity_text = input("Enter quantity: ")
price = float(price_text)
quantity = int(quantity_text)
total_cost = price * quantity
if price_text == "1.5" and quantity_text == "4":
    print("Total cost: £6.0")
elif price_text == "2.5" and quantity_text == "4":
    print("Total cost: £10.0")
else:
    print("Total cost: £0.0")
""",
        7,
    )

    assert issues == ["Printed output must use all entered value variables."]


def test_interactive_construct_issues_reject_floor_division_output_chain() -> None:
    issues = _construct_issues(
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

    assert "Printed result must come from calculations that use +, *, /." in issues
    assert "Printed result must not use //." in issues
