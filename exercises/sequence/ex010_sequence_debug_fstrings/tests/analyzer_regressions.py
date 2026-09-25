"""Repository-only regression cases for the ex010 sequence analyzer."""

from __future__ import annotations

import ast
from dataclasses import dataclass

from exercise_runtime_support.exercise_test_support import load_exercise_test_module

_CHECKS = load_exercise_test_module("ex010_sequence_debug_fstrings", "construct_checks")


@dataclass(frozen=True)
class RegressionCase:
    """One synthetic analyzer case and its expected result."""

    name: str
    source: str
    accepted: bool
    expected_issue_fragments: tuple[str, ...] = ()
    expected_payload_names: frozenset[str] | None = None
    exercise_no: int | None = None


CASES: tuple[RegressionCase, ...] = (
    RegressionCase(
        name="shadowed-print",
        source=(
            "print = lambda value: None\n"
            "name = 'Sam'\n"
            "print(f'Welcome, {name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("protected name 'print'", "Lambda"),
    ),
    RegressionCase(
        name="shadowed-input",
        source=(
            "input = 'popcorn'\n"
            "snack = input\n"
            "print(f'You chose {snack} for break time.')\n"
        ),
        accepted=False,
        expected_issue_fragments=("protected name 'input'",),
    ),
    RegressionCase(
        name="builtins-mutation",
        source=(
            "import builtins\n"
            "builtins.print = print\n"
            "name = 'Sam'\n"
            "print(f'Welcome, {name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("Imports", "Attribute"),
    ),
    RegressionCase(
        name="protected-builtin-rebinding",
        source=(
            "int, float, round, str = 1, 2.0, 3, 'x'\n"
            "name = 'Sam'\n"
            "print(f'Welcome, {name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("protected name",),
    ),
    RegressionCase(
        name="function-wrapper",
        source=(
            "def make_message(name):\n"
            "    return f'Welcome, {name}!'\n"
            "name = 'Sam'\n"
            "print(make_message(name))\n"
        ),
        accepted=False,
        expected_issue_fragments=("FunctionDef", "Arbitrary call"),
        expected_payload_names=frozenset(),
    ),
    RegressionCase(
        name="lambda-wrapper",
        source=(
            "name = 'Sam'\n"
            "print((lambda: f'Welcome, {name}!')())\n"
        ),
        accepted=False,
        expected_issue_fragments=("Lambda", "Arbitrary call"),
        expected_payload_names=frozenset(),
    ),
    RegressionCase(
        name="dead-conditional-fstring",
        source=(
            "name = 'Sam'\n"
            "if False:\n"
            "    print(f'Welcome, {name}!')\n"
            "print('plain')\n"
        ),
        accepted=False,
        expected_issue_fragments=("control flow",),
    ),
    RegressionCase(
        name="conditional-expression-fstring",
        source=(
            "name = 'Sam'\n"
            "message = f'Welcome, {name}!' if name else 'fallback'\n"
            "print(message)\n"
        ),
        accepted=False,
        expected_issue_fragments=("IfExp",),
    ),
    RegressionCase(
        name="dead-assignment-fstring-is-not-payload",
        source=(
            "name = 'Sam'\n"
            "unused = f'Welcome, {name}!'\n"
            "print('plain')\n"
        ),
        accepted=True,
        expected_payload_names=frozenset(),
    ),
    RegressionCase(
        name="subscript-lookup",
        source=(
            "values = ['Sam']\n"
            "print(f'Welcome, {values[0]}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("List", "Subscript"),
    ),
    RegressionCase(
        name="attribute-lookup",
        source=(
            "class Person:\n"
            "    name = 'Sam'\n"
            "person = Person()\n"
            "print(f'Welcome, {person.name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("ClassDef", "Attribute", "Arbitrary call"),
    ),
    RegressionCase(
        name="arbitrary-call",
        source=(
            "name = str('Sam')\n"
            "print(f'Welcome, {name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("Arbitrary call",),
    ),
    RegressionCase(
        name="nonempty-format-spec",
        source=(
            "name = 'Sam'\n"
            "print(f'Welcome, {name:>10}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("format specifications",),
    ),
    RegressionCase(
        name="boolop",
        source=(
            "name = 'Sam'\n"
            "flag = name and name\n"
            "print(f'Welcome, {name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("BoolOp",),
    ),
    RegressionCase(
        name="compare",
        source=(
            "name = 'Sam'\n"
            "print(f'Welcome, {name}' if name == 'Sam' else 'fallback')\n"
        ),
        accepted=False,
        expected_issue_fragments=("Compare", "IfExp"),
    ),
    RegressionCase(
        name="augassign",
        source=(
            "name = 'Sam'\n"
            "name += '!'\n"
            "print(f'Welcome, {name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("AugAssign",),
    ),
    RegressionCase(
        name="named-expression",
        source=(
            "name = (message := 'Sam')\n"
            "print(f'Welcome, {name}!')\n"
        ),
        accepted=False,
        expected_issue_fragments=("NamedExpr",),
    ),
    RegressionCase(
        name="keyword-fstring-is-not-payload",
        source=(
            "name = 'Sam'\n"
            "print('Welcome!', end=f'{name}', flush=f'{name}', file=f'{name}')\n"
        ),
        accepted=True,
        expected_payload_names=frozenset(),
    ),
    RegressionCase(
        name="annassign-valid",
        source=(
            "name: str = 'Sam'\n"
            "print(f'Welcome, {name}!', end='', flush=True)\n"
        ),
        accepted=True,
        expected_payload_names=frozenset({"name"}),
        exercise_no=1,
    ),
    RegressionCase(
        name="tuple-target-valid",
        source=(
            "name, unused = 'Sam', 'ignored'\n"
            "print(f'Welcome, {name}!', end='')\n"
        ),
        accepted=True,
        expected_payload_names=frozenset({"name"}),
        exercise_no=1,
    ),
    RegressionCase(
        name="empty-format-spec-valid",
        source=(
            "goals = 4\n"
            "print(f'You scored {goals:} goals today.')\n"
        ),
        accepted=True,
        expected_payload_names=frozenset({"goals"}),
        exercise_no=7,
    ),
    RegressionCase(
        name="input-prompt-alias-valid",
        source=(
            "prompt = 'Type your favourite snack: '\n"
            "snack = input(prompt)\n"
            "print(f'You chose {snack} for break time.')\n"
        ),
        accepted=True,
        expected_payload_names=frozenset({"snack"}),
        exercise_no=5,
    ),
    RegressionCase(
        name="input-keyword-valid",
        source=(
            "name = input(prompt='Enter your first name: ')\n"
            "town = input(prompt='Enter your town: ')\n"
            "print(f'Hello {name} from {town}.')\n"
        ),
        accepted=True,
        expected_payload_names=frozenset({"name", "town"}),
        exercise_no=6,
    ),
)


def run_regressions() -> list[str]:
    """Run every synthetic analyzer case and return human-readable failures."""
    failures: list[str] = []
    for case in CASES:
        failures.extend(_run_case(case))
    return failures


def _run_case(case: RegressionCase) -> list[str]:
    failures: list[str] = []
    tree = ast.parse(case.source)
    analysis = _CHECKS.analyze_sequence(tree)
    if case.accepted:
        if analysis.issues:
            failures.append(f"{case.name}: unexpected issues {analysis.issues!r}")
    else:
        failures.extend(_missing_issue_failures(case, analysis.issues))
    if case.expected_payload_names is not None:
        actual_names = analysis.final_payload_formatted_names()
        if actual_names != case.expected_payload_names:
            failures.append(
                f"{case.name}: positional payload names {actual_names!r} != "
                f"{case.expected_payload_names!r}"
            )
    if case.exercise_no is not None:
        task_issues = _CHECKS.construct_issues(tree, case.exercise_no)
        if task_issues:
            failures.append(f"{case.name}: unexpected task issues {task_issues!r}")
    return failures


def _missing_issue_failures(
    case: RegressionCase,
    issues: tuple[str, ...],
) -> list[str]:
    return [
        f"{case.name}: missing issue containing {fragment!r}; got {issues!r}"
        for fragment in case.expected_issue_fragments
        if not any(fragment in issue for issue in issues)
    ]


def main() -> int:
    """Run the repository-only regression suite."""
    failures = run_regressions()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(f"{len(CASES)} analyzer regression cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["CASES", "RegressionCase", "main", "run_regressions"]
