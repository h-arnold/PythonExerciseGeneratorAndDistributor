"""Repository-only construct regressions for ex007, excluded from grading bundles."""

from __future__ import annotations

import ast

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_EXERCISE_KEY = "ex007_sequence_debug_casting"
construct_checks = load_exercise_test_module(_EXERCISE_KEY, "construct_checks")
ex007 = load_exercise_test_module(_EXERCISE_KEY, "expectations")


def _construct_issues(code: str, exercise_no: int) -> list[str]:
    rules = ex007.EX007_INTERACTIVE_CONSTRUCTS[exercise_no]
    return construct_checks.interactive_construct_issues(
        ast.parse(code),
        expected_input_count=len(ex007.EX007_INPUT_CASES[exercise_no][0]["inputs"]),
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


def test_interactive_construct_issues_reject_hardcoded_prints_with_decoy_calculation() -> (
    None
):
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


def test_straightline_input_casts_allow_nested_input_same_line_and_reassignment() -> (
    None
):
    cases = (
        "age_text=input('Enter your age: '); age=int(age_text); print('Next year you will be '+str(age+1))",
        "age=input('Enter your age: '); age=int(age); age=age+1; print('Next year you will be '+str(age))",
        "age=int(input('Enter your age: ')); next_age=age+1; print('Next year you will be', next_age)",
    )
    for code in cases:
        assert _construct_issues(code, 3) == []


def test_sequential_provenance_uses_print_time_snapshot() -> None:
    valid = "count=3; message='You have '+str(count)+' pens'; print(message); message=str('unused')"
    future = "count=3; message='You have 3 pens'; print(message); message=str(count)"
    assert construct_checks.printed_output_has_call(ast.parse(valid), "str")
    assert not construct_checks.printed_output_has_call(ast.parse(future), "str")


def test_static_cast_must_join_the_original_numeric_value_into_printed_text() -> None:
    assert not construct_checks.printed_output_has_call(
        ast.parse("count=3; print(str('You have 3 pens'))"), "str"
    )
    assert not construct_checks.printed_output_has_call(
        ast.parse("price=7.5; print('Total price: £'+str('7.5'))"), "str"
    )
    assert construct_checks.printed_output_has_call(
        ast.parse(
            "price=7.5; price_text=str(price); print('Total price: £'+price_text)"
        ),
        "str",
    )
    for code in (
        "count=3; print('You have 3 pens'+str(count)*0)",
        "price=7.5; print('Total price: £7.5'+str(price)*0)",
    ):
        assert not construct_checks.printed_output_has_call(ast.parse(code), "str")


def test_output_comparison_preserves_words_and_order_but_accepts_wrapping() -> None:
    expected = "Enter your age: Next year you will be 15"
    assert ex007.outputs_match("Enter your age: \nNext year you will be 15", expected)
    assert ex007.outputs_match("You\nhave 3\npens", "You have 3 pens")
    assert ex007.outputs_match("Enter your age:Next year you will be 15", expected)
    assert not ex007.outputs_match("Youhave 3 pens", "You have 3 pens")
    assert not ex007.outputs_match("You have 15 pens", "You have 3 pens")


def test_fractional_average_and_bill_cases_distinguish_truncating_casts() -> None:
    average_outputs = [case["expected_output"] for case in ex007.EX007_INPUT_CASES[8]]
    bill_outputs = [case["expected_output"] for case in ex007.EX007_INPUT_CASES[10]]
    assert any(
        "Average score: 1.6666666666666667" in output for output in average_outputs
    )
    assert any("Each person pays: £5.6375" in output for output in bill_outputs)


def test_equivalent_fahrenheit_and_tip_formulas_need_only_taught_casts_and_output_flow() -> (
    None
):
    fahrenheit = "temp=input('C:'); c=float(temp); f=c/(5/9)+32; print('Temperature in Fahrenheit: '+str(f))"
    tip_split = "bill=input('Bill:'); people=input('People:'); total=float(bill)*1.1; each=total/int(people); print(f'Each person pays: £{each}')"
    assert _construct_issues(fahrenheit, 6) == []
    assert _construct_issues(tip_split, 10) == []


def test_average_requires_real_division_in_the_printed_calculation() -> None:
    decorative = (
        "total_distance=7; days=2; print('Average per day: '+str(3.5+0*1)+' km')"
    )
    future = "total_distance=7; days=2; average=3.5; print('Average per day: '+str(average)+' km'); average=7/days"
    assert not construct_checks.printed_output_has_source_operator(
        ast.parse(decorative), ast.Div
    )
    assert not construct_checks.printed_output_has_source_operator(
        ast.parse(future), ast.Div
    )


def test_augmented_assignments_keep_source_provenance() -> None:
    average = "total_distance=7; days=2; average=total_distance; average/=days; print('Average per day: '+str(average)+' km')"
    score_average = "s1=int(input('1:')); s2=int(input('2:')); s3=int(input('3:')); total=s1; total+=s2; total+=s3; average=total/3; print('Average score: '+str(average))"
    assert construct_checks.printed_output_has_source_operator(
        ast.parse(average), ast.Div
    )
    assert _construct_issues(score_average, 8) == []


def test_zero_weight_casts_and_unrelated_division_do_not_satisfy_tasks() -> None:
    static_average = (
        "total_distance=7; days=2; print('Average per day: '+str(3.5+0/1)+' km')"
    )
    assert not construct_checks.printed_output_has_source_operator(
        ast.parse(static_average), ast.Div
    )


def test_average_division_accepts_literal_operand_and_aliases_but_rejects_dummy_math() -> (
    None
):
    positives = (
        "total_distance=7; average=total_distance/2; print('Average per day: '+str(average)+' km')",
        "days=2; average=7/days; print('Average per day: '+str(average)+' km')",
        "total_distance=7; days=2; average=total_distance/days; print('Average per day: '+str(average)+' km')",
    )
    negatives = (
        "total_distance=7; days=2; zero=0; one=1; print('Average per day: '+str(3.5+zero/one)+' km')",
        "total_distance=7; days=2; print('Average per day: '+str(3.5+0/1)+' km')",
    )
    for code in positives:
        assert construct_checks.printed_output_has_source_operator(
            ast.parse(code), ast.Div
        )
    for code in negatives:
        assert not construct_checks.printed_output_has_source_operator(
            ast.parse(code), ast.Div
        )


def test_augmented_zero_multiplication_does_not_retain_dead_cast_provenance() -> None:
    dead_text = "count=3; text=str(count); text*=0; print('You have 3 pens'+text)"
    assert not construct_checks.printed_output_has_call(ast.parse(dead_text), "str")


def test_harmless_arithmetic_identities_keep_the_live_calculation() -> None:
    cases = (
        "distance=7; days=2; average=distance/days+0; print(str(average))",
        "distance=7; days=2; average=distance/days*1; print(str(average))",
        "distance=7; days=2; average=distance/days; average*=1; print(str(average))",
    )
    for code in cases:
        assert construct_checks.printed_output_has_source_operator(
            ast.parse(code), ast.Div
        )
