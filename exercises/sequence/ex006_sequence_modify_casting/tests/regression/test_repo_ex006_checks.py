"""Repository-only regressions for ex006's provenance and transcript checks."""

from __future__ import annotations

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_checks = load_exercise_test_module("ex006_sequence_modify_casting", "checks")


def test_valid_alternate_expression_shapes_preserve_live_cast_provenance() -> None:
    valid_sources = [
        (1, 'a="5"; b="10"; total=int(a)+int(b); print(total)'),
        (1, 'a="5"; b="10"; a=int(a); b=int(b); a+=b; print(a)'),
        (4, 'score=500; score=str(score); message="Your score is "+score; print(message)'),
        (6, 'num=int(input("Enter number:")); num=num*2; print(num)'),
        (6, 'num=input("Enter number:"); num=int(num); num*=2; print(num)'),
        (
            7,
            'price=float(input("Enter price:")); total=price+price; '
            'message=str(total); print("Two items cost: "+message)',
        ),
        (
            8,
            'width="10"; height="5"; w=int(width); h=int(height); '
            'area=w*h; print("Area: "+str(area))',
        ),
    ]
    assert all(_checks.complete(task, source) for task, source in valid_sources)


def test_casts_do_not_survive_overwrite_or_precede_original_values() -> None:
    invalid_sources = [
        (5, "temperature=25.9; temperature=int(temperature); temperature=25; print(temperature)"),
        (5, "temperature=25.9; temperature=25; print(temperature); temperature=int(temperature)"),
        (1, 'a="5"; b="10"; a=5; b=10; a=int(a); b=int(b); print(a+b)'),
    ]
    assert not any(_checks.complete(task, source) for task, source in invalid_sources)


def test_both_source_values_must_affect_the_calculated_result() -> None:
    valid_sources = [
        (1, 'a="5"; b="10"; print(int(a)+int(b))'),
        (1, 'a="5"; b="10"; total=int(a)+int(b); print(total)'),
        (8, 'width="10"; height="5"; print("Area:", int(width)*int(height))'),
        (8, 'width="10"; height="5"; w=int(width); h=int(height); area=w*h; print("Area:", area)'),
    ]
    neutralized_sources = [
        (1, 'a="5"; b="10"; print(int(a)*3+int(b)*0)'),
        (8, 'width="10"; height="5"; print("Area:", int(width)*5+int(height)*0)'),
    ]
    assert all(_checks.complete(task, source) for task, source in valid_sources)
    assert not any(_checks.complete(task, source) for task, source in neutralized_sources)


def test_tuple_and_list_assignment_bind_rhs_provenance_in_parallel() -> None:
    valid_sources = [
        (1, 'a,b="5","10"; print(int(a)+int(b))'),
        (1, 'a="5"; b="10"; a,b=int(a),int(b); print(a+b)'),
        (1, 'a="5"; b="10"; [a,b]=[int(a),int(b)]; print(a+b)'),
        (8, 'width,height="10","5"; print("Area:",int(width)*int(height))'),
        (
            8,
            'width="10"; height="5"; [w,h]=[int(width),int(height)]; area=w*h; print("Area:",area)',
        ),
    ]
    assert all(_checks.complete(task, source) for task, source in valid_sources)


def test_exercise4_requires_live_concatenation_not_an_unused_plus() -> None:
    valid = 'score=500; score=str(score); message="Your score is "+score; print(f"{message}")'
    invalid = 'score=500; score=str(score); unused=""+""; print(f"Your score is {score}")'
    assert _checks.complete(4, valid)
    assert not _checks.complete(4, invalid)


def test_input_prompt_and_result_segments_allow_boundary_whitespace_only() -> None:
    expected = ["Enter number:", "12"]
    assert _checks.matches_segments("Enter number:12", expected)
    assert _checks.matches_segments("Enter number: 12", expected)
    assert _checks.matches_segments("Enter  number:12", expected)
    assert _checks.matches_segments("Enter\nnumber:12", expected)
    assert not _checks.matches_segments("Enter number:120", expected)
    assert not _checks.matches_segments("12Enter number:", expected)
    assert not _checks.matches_segments("Enter number:12 extra", expected)
