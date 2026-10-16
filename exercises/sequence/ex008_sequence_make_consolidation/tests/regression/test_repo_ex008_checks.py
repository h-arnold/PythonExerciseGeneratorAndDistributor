"""Repository-only validator regressions, excluded from hidden grading bundles."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_checks = load_exercise_test_module("ex008_sequence_make_consolidation", "checks")
construct_errors = _checks.construct_errors
output_errors = _checks.output_errors
capture_interactive_events = _checks.capture_interactive_events
interactive_event_errors = _checks.interactive_event_errors


@pytest.mark.parametrize(
    ("part", "code"),
    [
        (
            1,
            "school, subject, group = 'Oakwood', 'Coding', 'Club'\nprint('Welcome to ' + school + ' ' + subject + ' ' + group + '!')",
        ),
        (
            2,
            "snack, quantity, price = 'muffins', 4, 2\nprint('Snack box:', snack)\nprint('Total cost:', quantity * price, 'pounds')",
        ),
        (
            3,
            "print('Your name please')\nname=input()\nprint('Hobby?')\nhobby=input()\nmessage='Hello '+name+'! Your hobby is '+hobby+'.'\nprint(message)",
        ),
        (
            4,
            "books=input('Books in one week?')\nbooks=int(books)\nweeks=int(input('How many weeks?'))\ntotal=books*weeks\nprint('Books read altogether: '+str(total))",
        ),
        (
            4,
            "books = int(input('Books read in one week: '))\nweeks = int(input('Number of weeks: '))\nprint('Books read altogether:', books * weeks)",
        ),
        (
            5,
            "distance=input('Distance?')\ndistance=float(distance)\ncount=int(input('How many walks?'))\nprint('Total distance: '+str(distance*count)+' km')",
        ),
        (
            5,
            "distance=float(input('Distance in km? '))\nwalks=int(input('How many walks? '))\nwalk_count=float(walks)\ntotal=distance*walk_count\nprint('Total distance:',total,'km')",
        ),
        (
            1,
            'school="Oakwood"\nsubject="Coding"\ngroup="Club"\nprint(f"Welcome to {school} {subject} {group}!")',
        ),
        (
            1,
            "school='Oakwood'\nschool_copy=school\nsubject='Coding'\ngroup='Club'\nprint('Welcome to '+school_copy+' '+subject+' '+group+'!')",
        ),
        (
            4,
            "books=int(input('Books?'))\nweeks=int(input('Weeks?'))\nprint(f'Books read altogether: {books*weeks}')",
        ),
        (
            5,
            "distance=float(input('Distance?'))\nwalks=int(input('Walks?'))\nprint(f'Total distance: {distance*walks} km')",
        ),
    ],
)
def test_valid_alternatives_are_accepted(part: int, code: str) -> None:
    assert not construct_errors(part, ast.parse(code))


@pytest.mark.parametrize(
    ("part", "code"),
    [
        (
            1,
            "school='Oakwood'\nsubject='Wrong'\ngroup='Club'\nprint('Welcome to Oakwood Coding Club!')",
        ),
        (
            1,
            "school='Oakwood'\nsubject='Coding'\ngroup='Club'\nschool='Other'\nprint('Welcome to '+school+' '+subject+' '+group+'!')",
        ),
        (
            2,
            "snack='muffins'\nquantity=8\nprice=1\ntotal=quantity*price\nprint('Snack box: muffins')\nprint('Total cost: 8 pounds')",
        ),
        (
            2,
            "snack='muffins'\nquantity=4\nprice=2\ntotal=quantity*price\ntotal=8\nprint('Snack box: '+snack)\nprint('Total cost: 8 pounds')",
        ),
        (3, "name=input()\nhobby=input()\nprint('Hello Aisha! Your hobby is drawing.')"),
        (
            3,
            "print('Name?')\na=int(input())\nprint('Hobby?')\nb=int(input())\nprint('Hello Aisha! Your hobby is drawing.')\nprint('Hello Leo! Your hobby is chess.')",
        ),
        (
            4,
            "books=int(input())\nweeks=int(input())\nunused=books*weeks\nprint('Books read altogether: 18')",
        ),
        (
            4,
            "print('Books per week?')\na=int(input())\nprint('Weeks?')\nb=int(input())\nunused=a*b\nprint('Books read altogether: 18')\nprint('Books read altogether: 0')\nprint('Books read altogether: 24')",
        ),
        (
            5,
            "distance=float(input())\ncount=input()\ncount=int(0)\nprint('Total distance: 7.5 km')",
        ),
        (
            1,
            "school='Oakwood'\nsubject='Coding'\ngroup='Club'\nprint('Welcome to '+'Oakwood'+' '+'Coding'+' '+'Club'+'!')",
        ),
        (
            2,
            "snack='muffins'\ntotal=4*2\nprint('Snack box:',snack)\nprint('Total cost:',total,'pounds')",
        ),
        (
            2,
            "snack='muffins'\nquantity=4\nprice=2\nunused=quantity*price\nprint('Snack box: muffins')\nprint('Total cost: 8 pounds')",
        ),
        (
            2,
            "snack='muffins'\nquantity=4\nprice=2\nprint('Snack box: '+'muffins')\nprint('Total cost:',4*2,'pounds')",
        ),
        (
            3,
            "name=input('Name?')\nhobby=input('Hobby?')\nprint('Hello '+name+'! Your hobby is '+hobby+'.')",
        ),
        (
            4,
            "books=int(input('Books?'))\nweeks=float(input('Weeks?'))\ntotal=int(int(books)*weeks)\nprint('Books read altogether:',total)",
        ),
        (
            5,
            "distance=float(input('Distance?'))\ncount=float(input('Walk count?'))\nprint(int(distance))\nprint('Total distance:',distance*count,'km')",
        ),
        (
            1,
            "school='Oakwood'\nsubject='Coding'\ngroup='Club'\nprint('Welcome to '+school+' Coding Club!')",
        ),
        (
            1,
            "school='Oakwood'\nsubject='Coding'\ngroup='Club'\nsubject=''\ngroup=''\nmessage='Welcome to '+school+' Coding Club!'\nprint(message)",
        ),
        (
            4,
            "books=int(input('Books?'))\nweeks=int(input('Weeks?'))\nunused=books*weeks\ntotal=books/(1/weeks)\nprint('Books read altogether:',total)",
        ),
        (
            4,
            "books=int(input('Books?'))\nweeks=float(input('Weeks?'))\ntotal=int(int(books)*weeks)\nprint('Books read altogether:',total)",
        ),
        (
            5,
            "distance=float(input('Distance?'))\ncount=float(input('Walk count?'))\nprint(int(distance))\nprint('Total distance:',distance*count,'km')",
        ),
    ],
)
def test_disconnected_or_overwritten_logic_is_rejected(part: int, code: str) -> None:
    assert construct_errors(part, ast.parse(code))


@pytest.mark.parametrize(
    ("part", "output", "inputs"),
    [
        (1, " Welcome   to Oakwood Coding Club! ", None),
        (2, "Snack box: muffins\nTotal cost: 8 pounds", None),
    ],
)
def test_static_output_ignores_horizontal_spacing(
    part: int, output: str, inputs: list[str] | None
) -> None:
    assert not output_errors(part, output, inputs)


@pytest.mark.parametrize(
    ("part", "output", "inputs"),
    [
        (1, "Welcome to Oakwood\nCoding Club!", None),
        (2, "Snack box: muffins Total cost: 8 pounds", None),
        (4, "Books read altogether: 180", ["6", "3"]),
        (4, "Books read altogether: 18\nBooks read altogether: 24", ["6", "3"]),
    ],
)
def test_static_boundaries_and_complete_results_are_enforced(
    part: int, output: str, inputs: list[str] | None
) -> None:
    assert output_errors(part, output, inputs)


@pytest.mark.parametrize(
    ("part", "code", "accepted"),
    [
        (
            3,
            "name=input('Name?')\nhobby=input('Hobby?')\nprint('Hello '+name+'! Your hobby is '+hobby+'.')",
            False,
        ),
        (
            3,
            "print('Name?')\nprint('Hobby?')\nname=input()\nhobby=input()\nprint('Hello '+name+'! Your hobby is '+hobby+'.')",
            False,
        ),
        (
            3,
            "name_prompt='Name?'\nhobby_prompt='Hobby?'\nprint(name_prompt)\nname=input()\nprint(hobby_prompt)\nhobby=input()\nprint('Hello '+name+'! Your hobby is '+hobby+'.')",
            True,
        ),
        (
            4,
            "books=int(input('Books?'))\nweeks=int(input('Weeks?'))\nprint('Books read altogether:',books*weeks)",
            True,
        ),
        (
            5,
            "distance=float(input('Distance?'))\nwalks=int(input('Walks?'))\nprint('Total distance:',distance*walks,'km')",
            True,
        ),
    ],
)
def test_prompt_order_and_input_cast_provenance(part: int, code: str, accepted: bool) -> None:
    errors = construct_errors(part, ast.parse(code))
    assert not errors if accepted else errors


def test_exercise3_rejects_additional_greeting() -> None:
    output = (
        "Name? Hobby? Hello Aisha! Your hobby is drawing. Hello Someone! Your hobby is something."
    )
    assert output_errors(3, output, ["Aisha", "drawing"], ["Name?", "Hobby?"])


@pytest.mark.parametrize(
    ("part", "output", "inputs", "prompts"),
    [
        (
            4,
            "Books read per week? Weeks? Books read\naltogether: 18",
            ["6", "3"],
            ["Books read per week?", "Weeks?"],
        ),
        (
            5,
            "Distance in km? Walks? Total distance:\n7.5 km",
            ["2.5", "3"],
            ["Distance in km?", "Walks?"],
        ),
    ],
)
def test_prompt_layout_and_wrapped_result_are_accepted(
    part: int, output: str, inputs: list[str], prompts: list[str]
) -> None:
    assert not output_errors(part, output, inputs, prompts)


@pytest.mark.parametrize(
    ("part", "code"),
    [
        (
            4,
            "books=int(input('Books?'))\nweeks=int(input('Weeks?'))\ntotal=weeks*books\nprint('Books read altogether:',total)",
        ),
        (
            5,
            "distance=float(input('Distance?'))\nwalks=int(input('Walks?'))\ntotal=walks*distance\nprint('Total distance:',total,'km')",
        ),
    ],
)
def test_reversed_multiplication_operands_are_valid(part: int, code: str) -> None:
    assert not construct_errors(part, ast.parse(code))


@pytest.mark.parametrize(
    ("part", "code"),
    [
        (
            1,
            "school='Oakwood'\nsubject='Coding'\ngroup='Club'\nmessage='Welcome to '\nmessage += school + ' ' + subject + ' ' + group + '!'\nprint(message)",
        ),
        (
            2,
            "snack='muffins'\nquantity=4\nprice=2\ntotal_cost=quantity\ntotal_cost *= price\nprint('Snack box:',snack)\nprint('Total cost:',total_cost,'pounds')",
        ),
        (
            4,
            "books=int(input('Books?'))\nweeks=int(input('Weeks?'))\ntotal_books=books\ntotal_books *= weeks\nprint('Books read altogether:',total_books)",
        ),
    ],
)
def test_augmented_assignment_updates_live_result(part: int, code: str) -> None:
    assert not construct_errors(part, ast.parse(code))


@pytest.mark.parametrize(
    ("part", "code"),
    [
        (
            1,
            "school='Oakwood'\nsubject='Coding'\ngroup='Club'\nprint(school*0+'Welcome to Oakwood Coding Club!')",
        ),
        (
            2,
            "snack='muffins'\nquantity=4\nprice=2\ntotal_cost=quantity*price*0+8\nprint('Snack box:',snack)\nprint('Total cost:',total_cost,'pounds')",
        ),
        (
            2,
            "snack='muffins'\nquantity=4\nprice=2\ntotal_cost=(quantity-quantity)*price+8\nprint('Snack box:',snack)\nprint('Total cost:',total_cost,'pounds')",
        ),
    ],
)
def test_neutralized_required_values_do_not_count_as_dependencies(part: int, code: str) -> None:
    assert construct_errors(part, ast.parse(code))


def _capture_code(tmp_path: Path, part: int, code: str, inputs: list[str]) -> list[tuple[str, str]]:
    notebook: dict[str, object] = {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {"tags": [f"exercise{part}"]},
                "source": code.splitlines(keepends=True),
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = tmp_path / "prompt_probe.ipynb"
    path.write_text(json.dumps(notebook))
    return capture_interactive_events(path, part, inputs)


@pytest.mark.parametrize(
    ("code", "inputs"),
    [
        (
            "print('Name?')\nname=input()\nprint('Enter your favourite hobby, '+name+':')\nhobby=input()\nprint('Hello '+name+'! Your hobby is '+hobby+'.')",
            ["Aisha", "drawing"],
        ),
        (
            "print('Enter',end=' ')\nprint('your name:')\nname=input()\nprint('Hobby?')\nhobby=input()\nprint('Hello '+name+'! Your hobby is '+hobby+'.')",
            ["Aisha", "drawing"],
        ),
    ],
)
def test_actual_dynamic_and_fragmented_print_prompts_are_captured(
    tmp_path: Path, code: str, inputs: list[str]
) -> None:
    events = _capture_code(tmp_path, 3, code, inputs)
    assert not interactive_event_errors(3, events, inputs)


@pytest.mark.parametrize(
    "code",
    [
        "# nothing attempted yet",
        "print('Name?')\nname=input()",
    ],
    ids=["comment_only", "single_input"],
)
def test_undersupplied_inputs_report_errors_without_raising(tmp_path: Path, code: str) -> None:
    events = _capture_code(tmp_path, 3, code, ["Aisha", "drawing"])
    assert interactive_event_errors(3, events, ["Aisha", "drawing"])
