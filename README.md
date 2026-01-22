# Python Tutor Exercises (prototype)

A teaching platform for secondary-school programming that keeps everything in the browser: students complete exercises inside notebooks, run code inline, and get autograding feedback. Teachers can generate new exercises quickly and bundle selected exercises into GitHub Classroom template repos.

This is a working prototype. The core workflow exists, but several pieces are incomplete (see Status below).

## What this project does

A teacher‑first toolchain that turns lesson plans into ready‑to‑run Python exercises—designed for secondary classrooms and low‑friction delivery.

For teachers:

- Generate complete, pedagogy‑aligned exercises in seconds (student notebook, solution mirror, and tests).
- Create exercises fast using the built-in Exercise Generation assistant (see [docs/exercise-generation.md](docs/exercise-generation.md)).
- Ship browser‑ready assignments your students can run inline (Codespaces now; Pyodide client‑side execution planned).
- Autograde student work with pytest so learners get immediate, actionable feedback.
- Create GitHub Classroom template repos with a CLI and consistent VS Code/devcontainer configs.

For students:

- Work inside a single, inline notebook cell with task, code, and debugger together.
- Get fast feedback from tests and clear, scaffolded prompts.
- No local installs required (when using Codespaces or the planned Pyodide runtime).

Why teachers will care:

- Slash setup time and eliminate “it works on my machine” problems ✅
- Spend classroom time teaching, not troubleshooting environments ✅
- Designed to be age‑appropriate and easy to adopt ✅

[Read about the pedagogical approach here](docs/pedagogy.md).

## How it works (plain‑English overview)

<figure style="display:inline-block;">
  <img src="docs/images/exercise-print-message.png" alt="Notebook editor showing a tagged exercise cell with expected output and a syntax error" style="transform:scale(0.75); transform-origin:top left; display:block;">
  <figcaption>Figure: Example student activity — a tagged cell with inline feedback.</figcaption>
</figure>

1. Each exercise is a notebook in [notebooks/](notebooks/), with a tagged cell like exercise1.
2. Tests in [tests/](tests/) extract that tagged cell and run it automatically.
3. Solution notebooks live in [notebooks/solutions/](notebooks/solutions/) and are used to verify the tests.
4. A CLI can bundle selected exercises into a GitHub Classroom template repo.

## Status

What works (mostly):

- Exercise scaffolding and tests via the generation workflow
- Tagged‑cell autograding ([tests/notebook_grader.py](tests/notebook_grader.py))
- Template repo creation with notebooks, tests, and VS Code settings
- GitHub Classroom workflow (template repo + autograding)

Known gaps / not fully working yet:

- The template repo currently includes solution notebooks (not suitable for students)
- Parts of the template‑repo population flow are untested
- Full VS Code for Web support needs a Pyodide‑based Python kernel integration

Where help is needed:

- Excluding solutions from student template repos
- Hardening the template‑repo CLI and improving test coverage
- VS Code for Web: building a Pyodide‑backed kernel that works with the official Jupyter extension

## Quickstart (exercise generation via Copilot Chat)

This repo includes a custom Copilot Chat mode for generating exercises.

1. Open this repository in VS Code.
2. Open Copilot Chat and pick the Exercise Generation mode (defined in [.github/agents/exercise_generation.md.agent.md](.github/agents/exercise_generation.md.agent.md)).
3. Describe the exercise (topic, difficulty, examples, and number of parts).
   <figure style="display:inline-block;">
     <img src="docs/images/exercise-generation-prompt.png" alt="Screenshot showing the Copilot Chat exercise generation prompt for creating an exercise" style="transform:scale(0.75); transform-origin:top left; display:block;">
     <figcaption>Figure: Copilot Chat prompt used to generate a new exercise.</figcaption>
   </figure>
4. Review the generated notebook, tests, and metadata for accuracy.
5. Verify the solution notebook passes tests:
   - [scripts/verify_solutions.sh](scripts/verify_solutions.sh) -q

More detail and expected structure: [docs/exercise-generation-cli.md](docs/exercise-generation-cli.md) — Instructions for using the exercise generation CLI tool to scaffold new Python exercises.

## Quickstart (create a GitHub Classroom template repo)

The template‑repo CLI packages selected exercises into a ready‑to‑use GitHub Classroom template.

1. Install uv and sync the project dependencies:
   - `python -m pip install --upgrade pip uv`
   - `uv sync`
2. Authenticate GitHub CLI:
   - `gh auth login`
3. Create a template repo (example: all sequence exercises):
   - `template_repo_cli create --construct sequence --repo-name sequence-exercises`
4. In GitHub Classroom, create a new assignment and select the template repo.

> Note: Running `pytest` without setting `PYTUTOR_NOTEBOOKS_DIR` will test the student notebooks (and will usually fail until exercises are completed). To verify instructor solutions locally, run:
>
> ```bash
> PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q
> ```

Full CLI reference: [docs/CLI_README.md](docs/CLI_README.md)

## Repository layout (high level)

- [notebooks/](notebooks/) — student exercise notebooks (tagged cells)
- [notebooks/solutions/](notebooks/solutions/) — instructor solutions
- [tests/](tests/) — pytest‑based autograding
- [scripts/](scripts/) — exercise generator + template‑repo CLI
- [exercises/](exercises/) — teacher materials
- [docs/](docs/) — documentation

## Documentation

- [docs/project-structure.md](docs/project-structure.md)
- [docs/testing-framework.md](docs/testing-framework.md)
- [docs/exercise-generation.md](docs/exercise-generation.md) — Guide to using the Exercise Generation assistant (Copilot) to create exercises quickly.
- [docs/exercise-generation-cli.md](docs/exercise-generation-cli.md) — Instructions for using the exercise generation CLI tool to scaffold new Python exercises.
- [docs/setup.md](docs/setup.md)
- [docs/CLI_README.md](docs/CLI_README.md)

## License

See [LICENSE](LICENSE) for details.
