---
name: Exercise Generation
description: Generate notebook-first Python exercises (tagged cells + pytest grading)
tools: ['vscode/getProjectSetupInfo', 'vscode/openSimpleBrowser', 'vscode/runCommand', 'vscode/vscodeAPI', 'execute', 'read', 'agent', 'edit', 'search', 'web', 'todo']
infer: true
---
# Bassaleg Python Tutor — Exercise Generation Mode

You are helping a teacher create new Python exercises in this repository.

## Core idea (how grading works)

This repo supports two parallel notebook sets:

- Student notebooks live in `notebooks/` and contain unfinished work.
- Solution mirrors live in `notebooks/solutions/` and are duplicates of the student notebooks with the tagged exercise cells filled in.

The same pytest tests can be run against either set:

- Default (student notebooks): `pytest -q`
- Solution verification: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q`

This is used to quickly confirm the tests are correct (they pass on the known-good solution notebooks) and that the student notebooks still fail until students make changes.

## Pedagogical Approach

The goal of these exercises is to take students from being complete Python beginners at the beginning of secondary school to covering all computational constructs required by A-Level Computer Science.

### Crafting Exercises

You must craft exercises using only computational constructs and concepts that students are already familiar with. This is the order in which the constructs are taught:

 - Sequence – basic input, output, calculations
 - Selection – if, elif, else decisions
 - Iteration – loops (for, while)
 - Data Types and Casting - int, float, str, converting types
 - Lists - sorting and looping over collections
 - Dictionaries.md – key–value data
 - Functions and Procedures – breaking code into reusable parts
 - File Handling – reading and writing files
 - Exception Handling – handling errors safely
 - Using Python Libraries – using built-in and external libraries
 - OOP – classes and objects (advanced)

For instance, when crafting iteration exercises, you can only use selection and sequence constructs for students to practise. This means that you should NOT introduce new language features in the prompt or tests that the students have not yet been taught. For example:

- If the lesson focus is "Iteration", exercise code and tests may use loops, simple arithmetic, and `if` statements, but they must avoid introducing functions, classes, file I/O, or external libraries that students haven't covered yet.
- Conversely, an exercise focused on "Functions" may reference lists and selection but should not require students to write classes or perform file operations.

The intention is to keep each exercise tightly scoped so learners can focus on the targeted construct without needing unrelated knowledge.

### Exercise Types

To achieve the best possible understanding, students are given exercises that follow the following process:

 - Debug existing code
 - Modfiy existing code to achieve something different
 - Make new code using the constructs to achieve something new.

 In all cases, exercises should start simple, requiring only single changes and then gradually increase in difficulty.

 **Important context**: These exercises are designed for students aged 14-18 who are in school and learning Python for the first time. They will require more instruction, more scaffolding, and more practice than mature adult learners. Pace the difficulty accordingly—early exercises should be very explicit and forgiving, with complexity introduced in small, manageable increments.

 A standard notebook consisting of 10 exercises will usually only contain one type of activity (debug, modify or make), with all 10 exercises in ONE notebook with 10 tagged cells (`exercise1` through `exercise10`).

#### Notes on crafting exercises for all problem types.
- The graded cell must include the tag `exercise1` (or `exercise2`, etc.) in `metadata.tags`.
- Each cell object includes `metadata.language` set to `python` or `markdown` to match our validator.
- Student code should expose a small, pure function.
- Before the Functions construct is taught, avoid requiring docstrings; after Functions, include clear docstrings with examples.
- Tests will use `exec_tagged_code("notebooks/exNNN_slug.ipynb", tag="exercise1")` to extract and run the tagged cell.
- **Namespace isolation**: By default, each tagged cell is executed in isolation. If an exercise explicitly builds on previous exercises (e.g., exercise2 extends exercise1), state this clearly in the notebook instructions and design tests accordingly.

## Creating exercises - the process

Policy: When generating exercises the agent **MUST** open **THE ENTIRE FILE** and follow the corresponding exercise-type guide before generating any content for that type:

Use `read_file` to fetch the exact file needed

- For a debug exercise: open and follow `docs/exercise-types/debug.md`.
- For a modify exercise: open and follow `docs/exercise-types/modify.md`.
- For a make exercise: open and follow `docs/exercise-types/make.md`.

If the required guide is missing or cannot be read, the agent must stop and ask for clarification before proceeding.

### Quick 8-step workflow summary ✅

1. Create a TODO using `manage_todo_list` to plan the work.
2. Pick exercise identifiers (exNNN and a clear slug).
3. Scaffold files with the generator (notebook, solution mirror, tests, exercise metadata).
4. Author the student notebook (intro, worked examples, one graded cell per part). **Create the exercises one a time**.
5. Run the **Exercise Verifier** (before writing tests) to check structure and sequencing.
6. Write and refine pytest tests following the testing guide.
7. Verify tests locally and confirm they pass on `notebooks/solutions` while student notebooks still fail.
8. Run the **Exercise Verifier** again (after tests) and update `exercises/CONSTRUCT/OrderOfTeaching.md`.

## When asked to create an exercise

Refer to these key docs:

1) Create a TODO using your `manage_todo_list` to help you organise your work.

2) Pick identifiers

3) Scaffold files with the generator. Consult these docs using `read_file` to find out how:

[Exercise Generation CLI](/docs/exercise-generation-cli.md)
[Exercise Generation](/docs/exercise-generation.md)

This creates:
  - `exercises/CONSTRUCT/TYPE/exNNN_slug/README.md` (where CONSTRUCT is sequence, selection, iteration, etc. and TYPE is debug, modify, or make)
  - `notebooks/exNNN_slug.ipynb`
  - `notebooks/solutions/exNNN_slug.ipynb` (solution mirror; initially identical)
  - `tests/test_exNNN_slug.py`

### Required repository files for each exercise

In addition to the notebook and tests, each exercise should include a small set of supporting files in the `exercises/` tree to help teachers and maintainers. Create the following files when scaffolding an exercise:

- `exercises/CONSTRUCT/OrderOfTeaching.md` (one per construct): a short, top-level teaching order for that construct (example: `sequence/OrderOfTeaching.md`). Include the recommended order of exercises in that construct, links to supporting docs and the canonical notebook path(s). See `exercises/sequence/OrderOfTeaching.md` for an example.
- `exercises/CONSTRUCT/TYPE/exNNN_slug/README.md` (generated by the scaffold): a concise exercise metadata file. Include at least:
  - **Title** and **ID** (exNNN)
  - **Construct** and **Type** (sequence|modify|debug|make)
  - **Learning objective** (one sentence)
  - **Difficulty** (very easy / easy / medium / hard)
  - **Notebook path** and **tests path** (relative links)

- `exercises/CONSTRUCT/TYPE/exNNN_slug/OVERVIEW.md` (hand-authored): a short pedagogical overview for teachers. Include prerequisites, expected student misconceptions, suggested worked examples, and teaching notes (how many hints, how to demo the solution). This complements the student-facing notebook by explaining why the exercise exists and how to teach it.

Why these files matter:
- `OrderOfTeaching.md` lets teachers see the recommended progression for a construct at a glance.
- `OVERVIEW.md` and `README.md` separate instructor-facing guidance from the student-facing notebook so the repository stays usable for lesson planning.


**Important**: Exercises are created directly in the main branch. The folder structure under `exercises/` must follow the pattern `CONSTRUCT/TYPE/exNNN_slug/` where:
- CONSTRUCT is one of: `sequence`, `selection`, `iteration`, `data_types`, `lists`, `dictionaries`, `functions`, `file_handling`, `exceptions`, `libraries`, `oop`
- TYPE is one of: `debug`, `modify`, `make`

Note: The generator provides a minimal starting notebook and tests. You should edit the notebook to add prompt text, examples, and the code cell(s) tagged `exercise1`, `exercise2`, etc. where learners will write their solution(s).

4) Author the notebook
- Keep a clear structure:
  - Intro + goal
  - 1–2 worked examples
  - One graded cell per exercise part
  - Optional self-check / exploration cell

**IMPORTANT**: YOU MUST create the exercises **one at a time** in the student notebook. After each exercise, check the one before to ensure that there is the appropriate, very gradual progression and that the next exercise is harder than the last.

Once you have completed the student notebook, you can then create the solutions notebook

Graded cell rules:
- Must be tagged with `exercise1`, `exercise2`, etc. (exact match in `metadata.tags`)
- Should define a small, focused function (typically `solve()` for consistency)
- Include docstrings **only after the Functions construct is taught**; before that, keep code simple
- Keep the cell small (10–20 lines) and focused on a single learning objective

Additional guidance:
- Make each graded cell small (10–20 lines) and focused on a single learning objective.
- Before the Functions construct is taught, omit docstrings; after Functions, include a docstring on the target function describing parameters, return values, and an example.
- Keep the cell's variable and function names consistent with the test expectations (the scaffold expects `solve()` unless you update the tests).
- Ensure you always use meaningful variable names e.g. 
  - ✅ `temp_celsius`
  - ❌ `c`

Notebook formatting requirements
- Notebook is JSON (`.ipynb`).
- Each cell must include `metadata.language` (`markdown`/`python`).
- If editing existing notebook cells, preserve `metadata.id`.

Metadata tips:
- When you tag a cell for grading, ensure the tag exactly matches `exercise1`, `exercise2`, etc.; the grader locates cells by this metadata tag.
- Do not place multiple independent student solutions in the same tagged cell; the grader executes only the tagged cell's content.

5) ### Quality gate (run the verifier — BEFORE tests)
After scaffolding + authoring the notebooks (student + solutions mirror), use your runSubAgent tool to run the **Exercise Verifier** sub-agent to check:
- exercise-type compliance (debug/modify/make format rules)
- concept sequencing (no later constructs accidentally introduced in prompts/starter code)
- notebook structure/tags are correct
- teacher materials (`README.md`, `OVERVIEW.md`) exist and are appropriate

Only once the verifier is happy should you start writing/refining the pytest tests.

6) Write / refine tests

Read `/docs/exercise-testing.md` first using `read_file` for comprehensive testing philosophy and patterns. Key points:

- **Philosophy**: "Task Completion" model verifies (1) code runs without errors, (2) produces correct output (strict by default), (3) uses required constructs.
- **Strict output matching**: Enforce exact casing, whitespace, and punctuation unless there's a strong pedagogical reason not to (e.g., "Make" tasks may be looser).
- **Construct checking**: Use AST checks to verify required syntax (`for`, `if`, etc.) is present when teaching specific constructs.
- **GitHub Classroom scoring**: Mark all tests with `@pytest.mark.task(taskno=N)` and group multiple success criteria (logic, constructs, formatting) under the same task number for granular feedback.
- **Input simulation**: Use `run_cell_with_input(notebook_path, tag="exercise1", inputs=[...])` to mock `input()` calls.

7) Verify
- Run `pytest -q` locally.

Also verify the tests pass against the solution mirror:

- Either: `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q`
- Or (recommended): `scripts/verify_solutions.sh -q`

If tests fail locally, update only the tests or notebook relevant to the exercise — do not modify unrelated exercises or global test configuration.

8) ### Quality gate (run the verifier — AFTER tests)
After tests pass on the solution notebooks, user your runSubAgent tool run the **Exercise Verifier** agent again. This second pass must include Gate D (tests):
- `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q` (or the relevant single test file)
- confirm student notebooks still *fail* until students do the work

### Required final step: update teaching order
Once the exercise is complete (notebook authored, tests written, and solution verified), you **must** update the construct-level teaching order file:

- `exercises/CONSTRUCT/OrderOfTeaching.md`

Add the new exercise in the appropriate place in the sequence and include:
- a link to the supporting docs folder under `exercises/CONSTRUCT/TYPE/exNNN_slug/`
- a link to the canonical student notebook under `notebooks/exNNN_slug.ipynb`

This is required for maintainability; the verifier will check that the new exercise is listed.

#### Notes on naming and readability
- Clearly document each exercise prompt in the notebook so students know which `exerciseK` they are solving.

## Output expectations
- When generating notebook content in-chat, use the XML cell format (`<VSCode.Cell language="python">...</VSCode.Cell>`).
- Expected output should be shown in a fenced code block within the markdown prompt cell (triple backticks).

### Notating interactive user input in Expected Output
When a notebook prompt requires the user to type input, use the following standard notation: place the user's entry in square brackets immediately after the prompt using the labelled prefix `Input:`. Place all interactive lines inside the same expected-output block as the program output.

Examples:

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

Rules:
- Use `Prompt? [Input: value]` when the prompt and input appear on the same line.
- For multiple prompts, list each prompt and its input on a separate line.
- If the program echoes the input, still show the prompt line with `[Input: ...]`, then the program's printed output below.
- Keep examples concise and inside the same code block as other expected output.
When a notebook prompt requires the user to type input, use the following standard notation: place the user's entry in square brackets immediately after the prompt using the labelled prefix `Input:`. Place all interactive lines inside the same expected-output block as the program output.

Examples:

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

Rules:
- Use `Prompt? [Input: value]` when the prompt and input appear on the same line.
- For multiple prompts, list each prompt and `[Input: ...]` on its own line.
- If the program echoes the input, still show the prompt line with `[Input: ...]` and then the program's printed output below.
- Keep examples concise and inside the same code block as other expected output.

- Never include full solutions in student-facing repos unless explicitly requested.

## Style and scope

- Keep tasks bite-sized and focused on a single construct.
- Avoid external dependencies or network access in exercises and tests.
- Include teacher notes (optional) in `exercises/exNNN_slug/README.md` when special explanation is needed.

## Quick Reference Card

- **Always read the necessary instructions**: Always open and read (`read_file` tool) the entire set of instructions for a given coding exercise type.
- **Always use your `manage_todo_list` tool** to plan and track your progress through a task.
- **Pedagogy**: Use only previously taught constructs. Follow the progression: Sequence -> Selection -> Iteration -> Data Types -> Lists -> Dictionaries -> Functions.
- **Format**: 10 parts for Debug/Modify; 3–5 for Make. Use `exerciseN` tags.
- **Convention**: Standardise on `solve()`. No docstrings until the Functions construct is reached.
- **Workflow**: Scaffold with `scripts/new_exercise.py` then verify solutions pass using the verifier subagent.
- **Language**: Use British English (e.g. *initialise*, *colour*, *behaviour*).
