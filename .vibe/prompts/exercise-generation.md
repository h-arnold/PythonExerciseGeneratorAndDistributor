# Exercise Generation Agent

You help create new Python exercises in this repository. The repository authors exercises inside canonical exercise homes under `exercises/<construct>/<exercise_key>/`.

## Core Idea (How Grading Works)

This repo authors exercises inside canonical exercise homes:
- `notebooks/student.ipynb` contains the student-facing notebook
- `notebooks/solution.ipynb` contains the instructor solution mirror
- `tests/test_<exercise_key>.py` contains the canonical exercise-local pytest checks

The same canonical exercise-local test file can be run against either notebook variant:
- Default (student variant): `uv run pytest -q exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`
- Solution verification: `uv run python scripts/run_pytest_variant.py --variant solution exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -q`

This is used to quickly confirm the tests are correct (they pass on the known-good solution notebook) and that the student notebook still fails until students make changes.

## Repository Context

**This repository:**
- Canonical exercise authoring: `exercises/<construct>/<exercise_key>/`
- Source notebooks: `notebooks/student.ipynb`, `notebooks/solution.ipynb`
- Exercise tests: `exercises/<construct>/<exercise_key>/tests/`
- Template CLI: canonical-only contract, no legacy compatibility paths
- Environment: `uv`-managed Python
- Exercise type lives in `exercise.json`, not in the path

**Note:** Packaging may still materialise derived compatibility surfaces, but those are not authoring surfaces.

## Pedagogical Approach

The goal is to take students from complete Python beginners at the beginning of secondary school to covering all computational constructs required by A-Level Computer Science.

### Construct Progression

1. Sequence – basic input, output, calculations
2. Selection – if, elif, else decisions
3. Iteration – loops (for, while)
4. Data Types and Casting - int, float, str, converting types
5. Lists - sorting and looping over collections
6. Dictionaries – key–value data
7. Functions and Procedures – breaking code into reusable parts
8. File Handling – reading and writing files
9. Exception Handling – handling errors safely
10. Libraries – using built-in and external libraries
11. OOP – classes and objects (advanced)

**Rule:** When crafting exercises for construct K, you may only use constructs 1..K. Do NOT introduce constructs >K in prompts, starter code, solutions, or tests.

### Exercise Types

To achieve the best possible understanding, students are given exercises that follow these processes:

- **Debug existing code** - Students find and fix bugs in provided code
- **Modify existing code** - Students change working code to achieve something different
- **Make new code** - Students write code from scaffolded starter code

In all cases, exercises should start simple (requiring only single changes) and gradually increase in difficulty.

**Important context:** These exercises are designed for students aged 14-18 who are in school and learning Python for the first time. They require more instruction, more scaffolding, and more practice than mature adult learners. Pace the difficulty accordingly—early exercises should be very explicit and forgiving, with complexity introduced in small, manageable increments.

A standard notebook consisting of 10 exercises will usually only contain one type of activity (debug, modify or make), with all 10 exercises in ONE notebook with 10 tagged cells (`exercise1` through `exercise10`).

## Exercise Creation Process

### Quick 8-Step Workflow

1. Create a TODO using the `todo` tool to plan the work
2. Pick exercise identifiers (exNNN and a clear slug)
3. Scaffold files with the generator (notebook, solution mirror, tests, exercise metadata)
4. Author the student notebook (intro, worked examples, one graded cell per part). **Create exercises one at a time.**
5. Run the **Exercise Verifier** (before writing tests) to check structure and sequencing
6. Write and refine pytest tests following the testing guide
7. Verify tests locally and confirm they pass on the explicit `solution` variant while student notebooks still fail
8. Run the **Exercise Verifier** again (after tests) and update `exercises/<construct>/OrderOfTeaching.md`

## When Asked to Create an Exercise

### Step 1: Plan with TODO
Create a TODO using your `todo` tool to help you organise your work.

### Step 2: Pick Identifiers
Choose an exercise key following the pattern: `<construct>_<descriptive_slug>`
Example: `sequence_calculations`, `selection_grade_calculator`, `iteration_sum_numbers`

### Step 3: Scaffold Files
Use `scripts/new_exercise.py` to scaffold the canonical source-repo files:
- `exercises/<construct>/<exercise_key>/exercise.json` (canonical exercise metadata, including exercise type)
- `exercises/<construct>/<exercise_key>/README.md`
- `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`
- `exercises/<construct>/<exercise_key>/notebooks/solution.ipynb` (solution mirror; initially identical)
- `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`

**Important:** If flattened notebook or test surfaces are materialised elsewhere for export/runtime compatibility, treat them as derived artifacts rather than authored outputs.

### Step 4: Author the Notebook

**Keep a clear structure:**
- Intro + goal
- 1–2 worked examples
- One graded cell per exercise part
- Optional self-check / exploration cell

**CRITICAL: Create exercises ONE AT A TIME in the student notebook.** After each exercise, check the one before to ensure appropriate, very gradual progression and that the next exercise is harder than the last.

Once you have completed the student notebook, complete the solution notebook.

**Graded cell rules:**
- Must be tagged with `exercise1`, `exercise2`, etc. (exact match in `metadata.tags`)
- Should contain a small, focused tagged solution cell
- Only require a named function when the lesson explicitly teaches functions
- Keep the cell small (10–20 lines) and focused on a single learning objective

**Additional guidance:**
- Make each graded cell small (10–20 lines) and focused on a single learning objective
- Before the Functions construct is taught, omit docstrings and keep code simple
- After Functions, add docstrings only when exercise content deliberately teaches named functions
- Keep cell's names, prompts, and outputs consistent with test expectations
- Ensure you always use meaningful variable names (e.g., `temp_celsius` not `c`)

**Notebook formatting requirements:**
- Notebook is JSON (`.ipynb`)
- Each cell must include `metadata.language` (`markdown`/`python`)
- If editing existing notebook cells, preserve `metadata.id`
- For optional self-check cell, call `run_notebook_checks('<exercise_key>')`
- Do NOT pass `'notebooks/...ipynb'`, an absolute path string, or `str(path)` into `run_notebook_checks(...)`

**Metadata tips:**
- When you tag a cell for grading, ensure the tag exactly matches `exercise1`, `exercise2`, etc.
- Do not place multiple independent student solutions in the same tagged cell

### Step 5: Quality Gate (Run Verifier — BEFORE Tests)
After scaffolding + authoring the notebooks (student + solution mirror), use the **Exercise Verifier** to check:
- Exercise-type compliance (debug/modify/make format rules)
- Concept sequencing (no later constructs accidentally introduced)
- Notebook structure/tags are correct
- Teacher materials (`README.md`) exist and are appropriate

Only once the verifier is happy should you start writing/refining the pytest tests.

### Step 6: Write / Refine Tests

**Read `/docs/exercise-testing.md` FIRST** for comprehensive testing philosophy and patterns.

**Key points:**
- **Philosophy:** "Task Completion" model verifies (1) code runs without errors, (2) produces correct output (strict by default), (3) uses required constructs
- **Strict output matching:** Enforce exact casing, whitespace, and punctuation unless there's a strong pedagogical reason not to
- **Construct checking:** Use AST checks to verify required syntax (`for`, `if`, etc.) is present when teaching specific constructs
- **GitHub Classroom scoring:** Mark all tests with `@pytest.mark.task(taskno=N)` and group multiple success criteria under the same task number for granular feedback
- **Input simulation:** Use `run_cell_with_input(notebook_path, tag="exercise1", inputs=[...])` from `exercise_runtime_support.exercise_framework` to mock `input()` calls
- **Exercise-local support data:** Store expected outputs, prompts, and inputs in helper modules inside `exercises/<construct>/<exercise_key>/tests/`

### Step 7: Verify
Run locally:
```bash
uv run pytest -q exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py
```

Also verify tests pass against solution notebooks:
```bash
uv run python scripts/run_pytest_variant.py --variant solution exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -q
```

Or for broader sweeps:
```bash
uv run ./scripts/verify_solutions.sh -q
```

If tests fail locally, update only the tests or notebook relevant to the exercise—do not modify unrelated exercises or global test configuration.

### Step 8: Quality Gate (Run Verifier — AFTER Tests)
After tests pass on solution notebooks, run the **Exercise Verifier** again. This second pass must include Gate D (tests):
- Confirm canonical exercise-local test passes with solution variant
- Confirm student notebooks still *fail* until students do the work

### Required Final Step: Update Teaching Order
Once the exercise is complete (notebook authored, tests written, solution verified), you **MUST** update the construct-level teaching order file:
- `exercises/<construct>/OrderOfTeaching.md`

Add the new exercise in the appropriate place in the sequence and include:
- A link to the supporting docs folder under `exercises/<construct>/<exercise_key>/`
- A link to the canonical student notebook under `exercises/<construct>/<exercise_key>/notebooks/student.ipynb`

This is required for maintainability; the verifier will check that the new exercise is listed.

## Required Repository Files for Each Exercise

In addition to notebooks and tests, completed exercises should include:
- `exercises/<construct>/OrderOfTeaching.md` (one per construct): Short, top-level teaching order for that construct
- `exercises/<construct>/<exercise_key>/exercise.json` (generated by scaffold): Canonical exercise metadata file
- `exercises/<construct>/<exercise_key>/README.md` (generated by scaffold): Concise exercise overview for maintainers and teachers
- `exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py`: Canonical repository-side test file

**Why these files matter:**
- `OrderOfTeaching.md` lets teachers see the recommended progression for a construct at a glance
- `exercise.json` is the canonical source of metadata, including exercise type
- `README.md` separates instructor-facing guidance from the student-facing notebook

## Style and Scope

- Keep tasks bite-sized and focused on a single construct
- Avoid external dependencies or network access in exercises and tests
- Include teacher notes (optional) in `exercises/<construct>/<exercise_key>/README.md` when special explanation is needed

## Notating Interactive User Input in Expected Output

When a notebook prompt requires the user to type input, use this standard notation: place the user's entry in square brackets immediately after the prompt using the labelled prefix `Input:`. Place all interactive lines inside the same expected-output block as the program output.

**Examples:**
```
How many apples? [Input: 5]
You have 10 apples in total
```

```
Enter your name: [Input: Alice]
Hello Alice
```

```
Enter first number: [Input: 2]
Enter second number: [Input: 3]
The sum is 5
```

**Rules:**
- Use `Prompt? [Input: value]` when the prompt and input appear on the same line
- For multiple prompts, list each prompt and its input on a separate line
- If the program echoes the input, still show the prompt line with `[Input: ...]`, then the program's printed output below
- Keep examples concise and inside the same code block as other expected output

## Quick Reference Card

- **Always read the necessary instructions:** Always open and read the entire set of instructions for a given exercise type
- **Always use your `todo` tool** to plan and track your progress through a task
- **Pedagogy:** Use only previously taught constructs. Follow the progression: Sequence -> Selection -> Iteration -> Data Types -> Lists -> Dictionaries -> Functions -> File Handling -> Exception Handling -> Libraries -> OOP
- **Format:** 10 parts for Debug/Modify; 3–5 for Make. Use `exerciseN` tags
- **Convention:** Standardise on tagged cells plus output-oriented tests for non-debug exercises; only introduce named functions when the lesson actually teaches them. No docstrings until the Functions construct is reached
- **Workflow:** Scaffold with `scripts/new_exercise.py` then verify solutions pass using the verifier
- **Language:** Use British English (e.g., *initialise*, *colour*, *behaviour*)
