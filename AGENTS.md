# Copilot Custom Instructions — PythonExerciseGeneratorAndDistributor

You are assisting in a classroom repository of Python exercises for secondary school students (ages 14-18).

> **Repository status**
> The source repository now uses the canonical exercise-local layout under `exercises/<construct>/<exercise_key>/`. Exported Classroom repositories may still flatten notebooks and tests during packaging, but those derived paths are not source-repository authoring surfaces.

## Project Overview

This repository provides notebook-based Python exercises with automated grading via pytest, designed for GitHub Classroom integration.

**Core concept**: Students work in Jupyter notebooks, writing code in metadata-tagged cells. The grading system extracts and executes these tagged cells using pytest, enabling automated feedback.

**Note on the Python environment**: This repository uses the `uv` tool to manage the Python environment. Use `uv sync` to create/update the project's virtual environment and run Python-related work through `uv` (or by activating the created `.venv` with `source .venv/bin/activate`). Avoid manipulating system Python or creating other virtual environments outside of `uv` so tests and tooling remain consistent.

## Quick Reference

**For exercise creation**: Use the exercise generation custom agent (`.github/agents/exercise_generation.md.agent.md`)

**Documentation (fetch on demand)**: Only read these files when a question specifically requires detailed information. Use `cat` or `sed -n` to fetch the exact file needed.

- `docs/project-structure.md` — project layout and file conventions
- `docs/execution-model.md` — source-of-truth contract for execution, discovery, runtime, variant, and export mapping behavior
- `docs/testing-framework.md` — how the grading and test system works
- `docs/exercise-generation-cli.md` — CLI for scaffolding new exercises
- `docs/setup.md` — installation and environment setup
- `docs/development.md` — contributor and development guidelines

## Repository Structure

```text
exercises/             # Canonical source-repo home for exercise-specific assets
  <construct>/<exercise_key>/
    exercise.json      # Exercise metadata (exercise type lives here, not in the path)
    notebooks/
      student.ipynb    # Canonical student notebook in the source repo
      solution.ipynb   # Canonical instructor solution notebook in the source repo
    tests/             # Canonical repository-side exercise-specific tests
tests/                 # Shared pytest suites and repository-level integration tests
  notebook_grader.py   # Core grading framework
  test_*.py            # Shared/integration tests, not canonical per-exercise authoring surfaces
scripts/               # Automation utilities
  new_exercise.py      # Exercise scaffolding tool
  run_pytest_variant.py# Explicit student/solution variant test runner
  verify_solutions.sh  # Convenience wrapper for solution-variant validation
docs/                  # Project documentation
```

### Naming and folder organisation

- File and module naming
  - Use snake_case for module and file names (e.g., `my_module.py`, `string_utils.py`).
  - Use CamelCase for classes (e.g., `HtmlParser`) and UPPER_SNAKE for constants.
  - Keep module surface area small and explicit: prefer small modules with a clear single responsibility.

- Packages and splitting modules
  - When a module grows or has distinct responsibilities, convert it to a package:
    - Create a folder `my_module/` with `__init__.py`.
    - Split parts into cohesive submodules (e.g., `my_module/core.py`, `my_module/_helpers.py`, `my_module/cli.py`).
    - Keep truly internal pieces prefixed with an underscore (e.g., `_helpers.py`).
    - Re-export the public API from `__init__.py` so callers use `from my_module import X`.
  - Aim for shallow, focused packages. If a package becomes complex, consider further subpackages.

- Type hints, guards and shared types
  - Put type guard helpers adjacent to the code they protect:
    - Prefer `module_typeguards.py`.
  - For cross-cutting TypedDicts or widely used type definitions, use a small `types/` package at repo root (e.g., `types/__init__.py`).
  - Keep type-only modules small and documented; avoid circular imports by placing shared TypedDicts in `types/` if necessary.

- Tests organisation
  - Mirror the package/module layout under `tests/`. Examples:
    - `my_module.py` -> `tests/test_my_module.py`
    - `my_module/` package -> `tests/test_my_module_api.py`, `tests/test_my_module_core.py`
  - Use pytest naming conventions: files `test_*.py`, functions `test_*`.
  - Keep tests fast and deterministic (no network, sleep, or randomness).
  - Each public behaviour should have positive and edge-case tests (follow repository testing standards).
  - For notebooks and exercises, canonical source-repo assets belong under `exercises/<construct>/<exercise_key>/`, with notebooks in `notebooks/{student,solution}.ipynb` and repository-side exercise tests in the exercise-local `tests/` directory. Flattened notebook mirrors and top-level `tests/test_exNNN_*.py` files are packaging outputs only, not the source-repo authoring layout.

- Practical rules of thumb
  - Small, well-documented modules are easier to test and review; prefer composition over monoliths.
  - Keep type guards and tiny helpers close to the code they protect to reduce cognitive overhead and avoid import cycles.
  - When splitting code, update and add tests at the same time and expose only the intended public API from packages.

## Coding Standards

### Concise Standards

- Python 3.11+; use modern type hints (e.g., `list[str]`).
- Fail Fast: **No defensive guards unless explicitly requested**. Better to find out something is broken than silently swallow errors!
- Docstrings required for public functions.
- Keep logic simple (KISS): low complexity, shallow nesting, short functions.
- Avoid duplication (DRY): extract shared helpers when logic repeats.
- No dead code: remove unused imports/vars; no commented-out code.
- Deterministic, fast tests: no randomness, time, or network.
- Prefer stdlib; avoid new deps unless necessary and justified.
- Match Ruff rules in `pyproject.toml` (E/F/W/I/UP/B/C90/LOG/PIE/RUF/SIM/PLR).
- Keep formatter changes unless the user says otherwise.
- **NEVER** silence linting errors without explicit authorisation from the user. If you feel that fixing the linting error would make the code less readable, then stop and ask for clarification.

### VERY IMPORTANT NOTE ON TESTING OUTPUT

Student variant tests **must always** fail in this repo. Soltution variant notebook tests **must always** pass. If you see a failing test, that is the expected behaviour for student variants. Do not attempt to fix or silence failing student tests. If you see a failing solution test, that is a problem that needs to be fixed.

### Python Style (for infrastructure code, not student exercises)

- **Language**: Python 3.11+
- **Linting**: Ruff (configured in `pyproject.toml`)
- **Type hints**: Use modern syntax (e.g., `list[str]` not `List[str]`)
- **Docstrings**: Required for public functions

Student exercise code in notebooks may omit these standards as exercises are designed for learning.

### TypeGuard best practices (typing and runtime checks) 🔧

- Prefer using `TypeGuard` functions to narrow runtime types instead of scattering `cast(...)` calls; they are clearer and Pylance understands them.
- Keep guards close to the code they protect: create a `_typeguards.py` or `<module>_typeguards.py` alongside the module they support (e.g., `scripts/template_repo_cli/core/_typeguards.py`). For cross-cutting types you can also create a small `types/` package or a shared `tests/typeguards/` package for test-only helpers.
- Name guards `is_<thing>` and keep each guard small and fast; they should check only the surface-level properties required for safe narrowing.
- Add unit tests for type guards (e.g., see `scripts/template_repo_cli/core/github.py` and its tests in `tests/template_repo_cli/test_github.py`).
- Example TypeGuard (place in the same module or in `<module>_typeguards.py`):

```py
from typing import TypeGuard

def is_notebook_cell(obj: object) -> TypeGuard[NotebookCell]:
    if not isinstance(obj, dict):
        return False
    cell_type = obj.get("cell_type")
    if cell_type is not None and not isinstance(cell_type, str):
        return False
    source = obj.get("source")
    if source is not None and not (isinstance(source, str) or isinstance(source, list)):
        return False
    if isinstance(source, list):
        for s in source:
            if not isinstance(s, str):
                return False
    metadata = obj.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return False
    return True
```

- Folder structure suggestion: for each module `module.py`, prefer a sibling `module_typeguards.py` (or `_typeguards.py`) containing guards for that module. Keep guards near code to avoid circular imports; if circular imports are possible, put small TypedDicts in a `types/` module or keep a tiny module-local guard instead.

### Testing Standards

- **Fast**: Each test should complete in < 1s
- **Deterministic**: No randomness, time-based checks, or network calls
- **Coverage**: At least 3 positive tests, 2 edge cases per exercise
- **Isolation**: Each tagged cell executes independently

### Notebook Standards

- **Format**: Standard `.ipynb` JSON
- **Cell metadata**: Generated notebooks include `metadata.language` ("python" or "markdown")
- **Tags**: Exact match required (e.g., `exercise1`, not `Exercise1` or `exercise_1`)
- **Tagged cells**: Use `exercise1`, `exercise2`, ... tags and align tests with the actual cell behaviour; there is no repository-wide `solve()` contract.
- **Checker cells**: Self-check notebook cells must call `run_notebook_checks('<exercise_key>')` with the canonical exercise key string. Do not pass notebook path strings such as `notebooks/foo.ipynb` or `str(path)` into that helper.

## Common Commands

```bash
# Enable venv - it doesn't automatically activate in your terminal instances for some reason
source .venv/bin/activate

# Run tests
uv run pytest -q

# Run tests against the solution variant
uv run python scripts/run_pytest_variant.py --variant solution -q

# Convenience wrapper for broader solution validation
uv run ./scripts/verify_solutions.sh -q

# Lint code
ruff check . --fix

```

## When Asked to Create Exercises

**Delegate to the exercise generation sub-agent** - it has specialised knowledge of pedagogical patterns, exercise types, and construct progression.

Do not create exercises manually. Use:

1. The exercise generation agent for authoring
2. `scripts/new_exercise.py` for scaffolding
3. The testing framework for grading

Canonical authoring note: exercise-specific assets belong under `exercises/<construct>/<exercise_key>/`, with source notebooks at `exercises/<construct>/<exercise_key>/notebooks/student.ipynb` and `exercises/<construct>/<exercise_key>/notebooks/solution.ipynb`, and exercise-specific tests under `exercises/<construct>/<exercise_key>/tests/`. Do not create or document new target paths of the form `exercises/<construct>/<type>/<exercise_key>/`; exercise type belongs in `exercise.json`. Flattened notebook or test surfaces, when present for export/runtime compatibility, are not the source-repo authoring layout.

## Working with the Grading System

The grading system (`tests/notebook_grader.py`) provides:

- `extract_tagged_code(notebook_path, *, tag="student")` - Extract source from tagged cells
- `exec_tagged_code(notebook_path, *, tag="student")` - Execute tagged cells and return namespace.
- `run_cell_and_capture_output(notebook_path, *, tag="student")` - Execute a tagged code cell and capture stdout; this is the primary helper for non-debug exercise behaviour checks.
- `run_cell_with_input(notebook_path, *, tag="student", inputs=[...])` - Execute a tagged code cell while supplying deterministic `input()` values.
- `get_explanation_cell(notebook_path, *, tag="explanation1")` - Read explanation or reflection markdown cells for debug-style checks.

Resolver contract note:

- Treat the canonical `exercise_key` as the notebook identity in generated self-check cells and author-facing guidance.
- If infrastructure code has already resolved a notebook to a `Path`, keep it as a `Path` when passing it into grader/runtime helpers. Do not convert the resolved path back into a path-like string before calling resolver-backed helpers.

When developing or validating repository-side exercises, run the canonical exercise-local tests directly with `uv run python scripts/run_pytest_variant.py --variant solution exercises/<construct>/<exercise_key>/tests/test_<exercise_key>.py -q`, or use `uv run ./scripts/verify_solutions.sh -q` for a broader solution pass.

See Testing Framework: `docs/testing-framework.md` for details.

## Calling Sub-Agents

When you need to perform a task that falls under the expertise of a sub-agent, you should delegate to that agent rather than trying to handle it yourself. This ensures that the task is completed with the appropriate level of focus and expertise.

The sub-agents you can call are (first-line names are case-sensitive):

- **Exercise Generation** — `.github/agents/exercise_generation.md.agent.md`  (first line: `Exercise Generation`)
- **Exercise Verifier** — `.github/agents/exercise_verifier.md.agent.md`  (first line: `Exercise Verifier`)
- **Implementer** — `.github/agents/implementer.md.agent.md`  (first line: `Implementer`)
- **Planner Reviewer** — `.github/agents/planner-reviewer.agent.md`  (first line: `Planner Reviewer`)
- **Tidy Code Reviewer** — `.github/agents/tidy_code_review.md.agent.md`  (first line: `Tidy Code Reviewer`)

## Implementation Workflow

For any significant code changes (defined as adding/modifying more than 1 function or class, or any non-trivial refactoring) that **IS NOT** related to student notebook, follow this workflow:

1. **Consider the size of the task**: If it's a large task requiring many changes, split the task into smaller chunks and update your TODO list manually.
2. **Delegate to the Implementer Agent**: Use the available sub-agent tool with the `Implementer` agent. Pass a detailed task description, including the scope of files to edit. If sub-agents are unavailable, complete the work directly.
    - *Prompt*: "Please implement [Feature X]. Relevant files: [A, B]. Criteria: [Z]."
3. **Review with Tidy Code Reviewer**: Once the implementer agent finishes, you **MUST** call the `Tidy Code Reviewer` agent to verify the changes. If sub-agents are unavailable, perform a careful self-review.
    - *Prompt*: "The implementer agent has completed task [X]. Please review the changes."
4. If there are significant changes, pass the *full* report back to the implementer to address the issues raised. Add any commentary or additional context you feel is necessary.
   1. If the changes are minor and can be fixed with a simple edit, you can make the change directly without going back to the implementer.
5. Repeat as many times as necessary to get a clear code review from the Tidy Code Reviewer.

**ALWAYS** follow this process unless the user explicitly directs you otherwise.
