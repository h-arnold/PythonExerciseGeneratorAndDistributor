# Exercise Quality Verifier

Canonical contract for `scripts/verify_exercise_quality.py`: the objective gate
set run against one exercise during authoring, or against the whole catalogue
with `--all`. The verifier is a fast pre-flight check; it is **not** a
substitute for reading the prompts or for the agent gates in
`.opencode/agents/exercise-reviewer.md` and
`.opencode/agents/exercise-test-reviewer.md`. Its gate letters are its own:
Gate F, G, H and I are the checker/expectations/variant/runtime checks, and they
do not correspond one-to-one with the reviewer agents' gate letters.

The gates read canonical exercise-local paths:

```text
exercises/<construct>/<exercise_key>/
  README.md
  exercise.json
  notebooks/student.ipynb
  notebooks/solution.ipynb
  tests/test_<exercise_key>.py
  tests/expectations.py
  tests/student_checker_support.py
```

plus the construct-level teaching order at `exercises/<construct>/OrderOfTeaching.md`.

## CLI

```bash
# One exercise
uv run python scripts/verify_exercise_quality.py ex011_sequence_gaps_consolidation

# Whole catalogue
uv run python scripts/verify_exercise_quality.py --all
```

| Option | Effect |
| --- | --- |
| `exercise_key` (positional) | Canonical exercise key. Required unless `--all`. |
| `--all` | Verify every exercise under `exercises/<construct>/`, one labelled section each. |
| `--construct`, `--type` | Override the construct/type inferred from `exercise.json`. Single-exercise mode only; rejected with `--all`. |
| `--skip-empty-checks` | Suppress **only** Gate F's empty-`CHECKS` error, for Phase 1 authoring before checker definitions exist. |
| `--repo-root` | Repository root; defaults to the detected checkout root. |

Exit codes: `0` when there are no `ERROR` findings (warnings are reported and
still exit `0`), `1` when at least one `ERROR` is reported, `2` from `argparse`
for invalid flag combinations.

Finding granularity: a `Finding` carries only severity, message and path. A
progression finding is emitted once per later construct whose first matching
pattern is found in a notebook's concatenated tagged-cell source, and once per
notebook surface, so several offending cells for the same construct collapse into
one finding, and no finding is attributed to a specific cell tag.

## Gate inventory

| Check | Inspects | Severity |
| --- | --- | --- |
| Canonical structure | `README.md`, `notebooks/student.ipynb`, `notebooks/solution.ipynb`, `tests/test_<exercise_key>.py` | `ERROR` |
| `OrderOfTeaching.md` | `exercises/<construct>/OrderOfTeaching.md` exists and mentions the exercise folder name or a notebook path | `ERROR` |
| Notebook structure, tags, student/solution parity | `metadata.language`, `exerciseN`/`explanationN` continuity, matching tagged surfaces | `ERROR` |
| Construct progression scan | Executable source of tagged task cells in both notebooks | `WARN` |
| Gate F | `tests/student_checker_support.py` exists, imports, and defines `CHECKS` as a `list` that is non-empty (only the empty-list case is suppressed by `--skip-empty-checks`) | `ERROR` |
| Gate G | `tests/expectations.py` exists and declares every part | `ERROR` |
| Gate G cross-check | Static/interactive declarations agree with `input()` usage in the solution notebook | `ERROR`, or `WARN` for a double declaration |
| Gate H | `PYTUTOR_ACTIVE_VARIANT` overrides in both self-checker cells | `ERROR` / `WARN` (see below) |
| Gate I | Runs the solution variant of the self-checker and reports failing checks | `ERROR` |

Gate I is skipped with a `WARN` whenever the Gate G cross-check reports an
`ERROR`, because `run_cell_and_capture_output` supplies no stdin and would block
forever on an `input()`-using cell classified as static.

## Construct progression scan

**Contract:** the scan reports a later construct only where it is **executable**
in a tagged `exerciseN` code cell of the student or solution notebook.

- **Scope**: code cells tagged `exercise1`, `exercise2`, … only. Untagged
  infrastructure cells (scratch pad, self-checker) are excluded.
- **Prose is not code**: comments, ordinary string literals, and the literal
  chunks of f-strings are blanked out before the patterns run. Offsets and line
  breaks are preserved, so layout-sensitive patterns still work. Real instances
  this removes include `# Use // for full hours and % for leftover minutes`
  (sequence ex012, `exercise7`), `# Ask for input, convert, calculate, and print.`
  (sequence ex015, `exercise3`), `print("Good try")` (selection ex002,
  `exercise18`), and `print(f"Small van for {passengers} passengers")`
  (selection ex003, `exercise2`).
- **f-string expressions are code**: since PEP 701 (Python 3.12) the tokenizer
  emits a replacement field as ordinary tokens, so `print(f"{len([1, 2])} items")`
  still warns about `len(`. Before 3.12 the whole f-string arrives as one string
  token and its replacement fields are blanked with the literal; the repository
  runtime pins Python 3.14.
- **Invalid debug cells are scanned, never skipped**: a tokenizer failure keeps
  the tokens read before the failure instead of discarding the cell, so a real
  later construct in intentionally broken debug code still warns. Text after the
  failure point is matched as code, which can add a warning but never hides one.
- **Token kinds are an allowlist**: only `NAME`, `NUMBER`, `OP`, `NEWLINE`, `NL`,
  `INDENT`, `DEDENT` and `ENDMARKER` count as executable. Every other kind is
  treated as prose, so a token kind added by a future Python release cannot
  invent new warnings.
- **Line offsets follow the tokenizer**: offsets are built from `io.StringIO`,
  not `str.splitlines`, because `tokenize` ends a line only at a newline while
  `splitlines` also breaks on `\r`, form feed, NEL and the Unicode line and
  paragraph separators.

### Casting is a sequence/selection prerequisite

`_CASTING_PREREQUISITE_CONSTRUCTS = frozenset({"sequence", "selection"})` waives
the `data_types` patterns (`int(`, `float(`, `str(`) for those two constructs
only:

- `exercises/sequence/OrderOfTeaching.md` teaches casting in
  `ex006_sequence_modify_casting` and `ex007_sequence_debug_casting`, part-way
  through the sequence strand.
- The selection strand compares values read from `input()`, so those casts must
  already have been taught. In
  `exercises/selection/ex002_selection_debug_if_then_else/notebooks/solution.ipynb`,
  17 of the 20 tagged cells cast their input before the conditional; the three
  that do not (exercises 5, 10 and 14) compare string input, which needs no
  cast.

The waiver is narrow: iteration, exceptions, and every other later construct
(lists, dictionaries, functions, file handling, libraries, oop) stay exactly as
strict as before.

> **📋 Verdict policy:** a progression finding is a prompt for review, not an
> instruction to edit the notebook. Do not remove legitimate teaching code to
> silence a warning.

Reference tests: `tests/test_verify_exercise_quality.py::TestProgressionScanExecutableConstructs`,
`::TestProgressionScanIgnoresNonExecutableTokenText`,
`::TestProgressionScanTokenizerLineOffsets`,
`::TestProgressionCastingPrerequisitePolicy`.

## Gate G — expectations module

**Contract:** `exercises/<construct>/<exercise_key>/tests/expectations.py` is the
single source of expected outputs, prompt text and input data for that exercise.
The exercise-local test file and `student_checker_support.py` must both load it
via `load_exercise_test_module(exercise_key, "expectations")` and must not repeat
its literals in private dicts. `exercises/sequence/ex011_sequence_gaps_consolidation/`
is the reference shape: static expectations for parts 1, 2, 4, 5, 6, 7 and input
cases for 3, 8, 9, 10, loaded by both its checker and its tests.

### Recognised conventions

Expectation dicts are module-level names matching `EX<N>_<CONVENTION>`, where `N`
is the exercise number (`ex011` → `EX011_…`). Coverage is the **union** of the
part keys of every recognised dict, so an exercise may split its expectations
across several shape-specific dicts.

| Family | Recognised suffixes | Declares |
| --- | --- | --- |
| Static | `EXPECTED_OUTPUTS`, `EXPECTED_STATIC_OUTPUT`, `EXPECTED_STATIC_OUTPUTS`, `EXPECTED_SINGLE_LINE`, `EXPECTED_MULTI_LINE`, `EXPECTED_NUMERIC`, `EXPECTED_PRINT_CALLS` | what a part prints without reading input |
| Interactive | `INPUT_CASES`, `INPUT_EXPECTATIONS`, `INTERACTIVE_CASES`, `EXPECTED_PROMPTS`, `PROMPT_STRINGS`, `INPUT_PROMPTS`, `EXERCISE_INPUTS`, `FORMAT_VALIDATION` | a runnable input case, or the prompts/inputs/post-input message it is driven with, for a part whose code calls `input()` |

Dicts in neither family — supplementary `EX<N>_EDGE_CASES` or
`EX<N>_ORIGINAL_PROMPTS` data, and reference aliases — count as neither coverage
nor a runnable input case.

Gate G reports an `ERROR` when no recognised dict exists, when every recognised
dict is empty, or when any part in `1..parts` is undeclared.

### Static/interactive classification

The cross-check compares each part's declarations against `input()` usage in the
solution notebook:

| Situation | Severity |
| --- | --- |
| Part calls `input()` but is declared only in static dicts | `ERROR` — the runtime self-check would hang |
| Part calls `input()` and is declared nowhere runnable | `ERROR` |
| Part calls `input()` and is declared in both families | `WARN` |
| Part does not call `input()` but is declared interactive | `ERROR` |

### Derived reference outputs

An entirely interactive exercise may publish a quick-reference static dict
computed from one of its interactive dicts. Such a dict is a
**reference alias**, not a second static declaration, so it is not reported as
the exercise being listed in both families. The alias predicate is deliberately
narrow: the dict must be a module-level comprehension keyed over an interactive
dict whose values are each case's `expected_output` unchanged. A hand-written
literal dict, or a comprehension that derives anything else (a concatenation, a
different case field), is an independent declaration and is still reported.

Shipped examples: `EX002_EXPECTED_OUTPUTS` in
`exercises/selection/ex002_selection_debug_if_then_else/tests/expectations.py` is
derived from `EX002_INPUT_CASES` and is the single expected-output lookup its
tests read, and `EX004_DERIVED_OUTPUTS` in
`exercises/selection/ex004_selection_modify_logical_operators/tests/expectations.py`
does the same.

### Enforcement

Two data rules are enforced across every exercise that ships `expectations.py`,
in `tests/test_exercise_expectation_data.py`, using the verifier's own
classification so there is a single definition:

1. No part may be declared in both families, unless the static dict is a
   value-for-value mirror of the input cases.
2. No static expected-output value may be an empty placeholder.

## Gate H — notebook variant overrides

**Contract:** the student self-checker cell may omit the
`PYTUTOR_ACTIVE_VARIANT` assignment, because the checker runtime resolves an unset
variable to the student variant (see the variant contract in
[execution-model.md](execution-model.md)). The solution self-checker cell must set
it, because that cell would otherwise read `student.ipynb`.

| Notebook | Assignment | Severity |
| --- | --- | --- |
| Student | omitted | no finding |
| Student | `'student'` | no finding |
| Student | anything else | `WARN` |
| Solution | omitted | `ERROR` |
| Solution | anything else | `ERROR` |

`scripts/exercise_scaffolder/base.py::build_check_answers_cell` emits exactly this
shape, and `tests/test_new_exercise.py` pins it.

> **⚠️ Residual risk:** the student default only applies when
> `PYTUTOR_ACTIVE_VARIANT` is unset **in that kernel**. The solution self-checker
> cell sets it to `solution`, and that value persists for the rest of the kernel
> session. A kernel that has run the solution self-checker and is then used for
> the student notebook will read `solution.ipynb` and report ✅ for unfinished
> work. Remedy: run the student self-checker in a fresh kernel (restart the
> kernel, or give the solution notebook its own kernel session). No notebook edit
> is required, and this is not a reason to add an explicit student assignment.
> Teachers see this as a self-checker symptom; see
> [../teachers/classroom-practices.md](../teachers/classroom-practices.md).

## Gate I — runtime self-check

Gate I sets `PYTUTOR_ACTIVE_VARIANT=solution`, runs `run_exercise_checks`, and
reports one `ERROR` per failing check, naming the exercise number and the check
issues. It restores the previous environment value afterwards, so it does not
change the variant for subsequent pytest runs in the same process.

Error handling is deliberately narrow, not fail-safe: only `ImportError`,
`LookupError`, and `ValueError` raised by the self-check are converted into a
single `ERROR` finding (`Runtime self-check raised an exception: …`). A missing
`tests/student_checker_support.py` is a `WARN`. Every other exception propagates
out of the verifier, so a broken checker or an environment problem fails the run
loudly instead of being reported as a check failure.

## Related commands

```bash
# Verifier gate set for one exercise, and for the catalogue
uv run python scripts/verify_exercise_quality.py ex011_sequence_gaps_consolidation
uv run python scripts/verify_exercise_quality.py --all

# Gate-set unit tests and the catalogue-wide expectation data guards
uv run pytest tests/test_verify_exercise_quality.py tests/test_exercise_expectation_data.py -q

# Solution-variant suite (student variants are expected to fail)
uv run python scripts/run_pytest_variant.py --variant solution -q
```