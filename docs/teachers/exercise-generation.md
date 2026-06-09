# Generating Exercises with GitHub Copilot

This guide explains how to use the **Exercise Generation** assistant in GitHub Copilot to create new Python exercises for students. This tool is designed to help you quickly create pedagogically sound exercises without needing to manually write all the boilerplate code.

- [Generating Exercises with GitHub Copilot](#generating-exercises-with-github-copilot)
  - [First Time Setup](#first-time-setup)
    - [What to expect after cloning (prompts \& tips)](#what-to-expect-after-cloning-prompts--tips)
  - [Using the Exercise Generation Assistant](#using-the-exercise-generation-assistant)
    - [1. Select the Agent](#1-select-the-agent)
    - [2. Crafting Your Prompt](#2-crafting-your-prompt)
      - [Example Scenario A: Reinforcing Recent Lessons](#example-scenario-a-reinforcing-recent-lessons)
      - [Example Scenario B: Targeting Misconceptions](#example-scenario-b-targeting-misconceptions)
    - [3. Iterating on Content](#3-iterating-on-content)
    - [4. Saving Your Work](#4-saving-your-work)
  - [Exercise Reviewer — quick quality checks 🔍](#exercise-reviewer--quick-quality-checks-)
  - [Best Practices](#best-practices)

## First Time Setup

If you are new to Visual Studio Code (VS Code) or GitHub Copilot, follow these steps to get ready:

1. **Create a GitHub account**: You will need a GitHub account so you can clone the repository and sign in to Copilot. If you don't have an account, sign up at <https://github.com>. Note: your organisation may require a Copilot subscription.

2. **Clone the repository**: In VS Code use **Source Control** → **Clone Repository**, or open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run **Git: Clone**. Paste your repository URL for `PythonExerciseGeneratorAndDistributor`. (If you already have a local copy, you can instead use **File > Open Folder...** and select the `PythonExerciseGeneratorAndDistributor` folder.) After opening the workspace, see the [What to expect after cloning (prompts & tips)](#what-to-expect-after-cloning-prompts--tips) section below for guidance on common VS Code prompts and recommended actions.

3. **Sign in to GitHub in VS Code**: Click the Accounts icon in the bottom-left of VS Code and sign in with your GitHub account so extensions (Copilot) can access it.

4. **Check Extensions**:
   - Click the **Extensions** icon in the left sidebar (it looks like four squares with one detached).
   - Search for "GitHub Copilot" and install **GitHub Copilot** and **GitHub Copilot Chat** if they are not already installed.

5. **Open Chat**: Click the **Chat** icon in the sidebar (a speech bubble) or press `Ctrl + Alt + I` (Windows) / `Cmd + Ctrl + I` (Mac) to open Copilot Chat.

6. **Select Exercise Generation chatmode**: In the Chat panel, open the model/agent selector (top of the chat window) and choose **Exercise Generation** so the assistant uses the repository-specific exercise templates and guidelines. If you don't see it, sign out and sign back in to Copilot or reload the window (`Ctrl+Shift+P` / `Cmd+Shift+P` → "Developer: Reload Window").

![Copilot Chat screenshot showing example prompts and the model selector](images/copilot-chat-example.png)

*Figure: Copilot Chat — the model/agent selector appears at the top of the chat panel (used to select **Exercise Generation**); the conversation area shows example prompts you can copy and edit.*

### What to expect after cloning (prompts & tips)

When you open the cloned repository in VS Code you may see a few helpful prompts — these are normal and aimed at making the workspace easier to work with. Here's what you might see and what to do:

- **Recommended extensions pop-up**: The workspace recommends extensions including `ms-python.python`, `ms-python.vscode-pylance`, `charliermarsh.ruff`, `github.copilot`, and `github.copilot-chat`. Installing these is recommended (particularly Copilot and Pylance) but you can decline if your school has restrictions.

- **Python interpreter / virtual environment prompt**: VS Code will try to use the interpreter at `${workspaceFolder}/.venv/bin/python` (configured in the workspace settings). If `.venv` doesn't exist yet, you'll be prompted to select an interpreter or create a virtual environment. Recommended quick setup:

  ```bash
  python -m pip install --upgrade pip uv
  uv sync
  ```

- **Test discovery prompt**: Because the workspace enables pytest in the workspace settings, VS Code may ask to enable test discovery; allow this if you want to run tests from the Test sidebar.

- **Format-on-save / code actions**: The workspace config enables `editor.formatOnSave` and code-actions-on-save for Python. If you prefer not to change files automatically, you can disable format-on-save in the Command Palette or your personal settings.

- **Debug configurations**: `launch.json` includes useful debug entries (run a single file or run pytest). These won't prompt you, but they appear in the Run & Debug view.

If any prompt looks unfamiliar, you can safely decline and follow the manual setup steps above — or consult your IT admin if your school restricts extension installation.

## Using the Exercise Generation Assistant

This repository includes a specialised helper called the **Exercise Generation** agent. It knows how our grading system works and how to structure exercises for our students.

### 1. Select the Agent

In the Chat panel you just opened:

- Look for the model/agent selector (usually at the top or bottom of the chat window).
- Select **Exercise Generation** (you might see it in a dropdown list or by typing `@Exercise Generation`).
- *Note: If you don't see it, ensure you have the repository folder open as your workspace root.*

### 2. Crafting Your Prompt

The most important step is asking the right question. The agent works best when you give it **teaching context**.

Instead of asking "Write a loop exercise", explain what the students need to practise.

#### Example Scenario A: Reinforcing Recent Lessons

*You want to solidify knowledge after a specific exercise.*

> **Prompt to copy:**
> "Please create a set of logical error debug tasks that build on the most common logical errors you might find when writing code similar to those in ex003"

**Why this works:**

- It references `ex003`, so the agent knows the difficulty level.
- It asks for "logical error debug tasks" (code that runs but gives the wrong answer), which forces students to read code carefully.

#### Example Scenario B: Targeting Misconceptions

*You want to address common mistakes you see in class.*

> **Prompt to copy:**
> "Please create me a set of debug exercises around the most common syntax errors that would crop up when attempting the tasks in the previous two modify activities."

**Why this works:**

- It asks for "syntax errors" (code that breaks/crashes).
- It contextualizes it to the "previous two modify activities", creating a realistic follow-up to their recent work.

### 3. Iterating on Content

The agent will generate a response, often including a plan or code snippets.

- **Too hard?** Reply: "Simplify the second task for a beginner."
- **Wrong focus?** Reply: "Less focus on math, more on string manipulation."
- **Need files?** Reply: "What command should I run to create these files?"

### 4. Saving Your Work

The Exercise Generation agent will scaffold the files and populate the content for you. Here is what happens and what you need to do.

**Create the file structure** — the agent runs this command for you:

```bash
uv run python scripts/new_exercise.py ex050 "My New Topic" \
  --construct sequence \
  --type modify \
  --slug my_topic
```

The scaffolder writes directly to `exercises/sequence/ex050_sequence_modify_my_topic/` with:

- `exercise.json` — exercise metadata (type is stored here, not in the folder path)
- `notebooks/student.ipynb` — the student-facing notebook
- `notebooks/solution.ipynb` — instructor solution mirror
- `tests/test_ex050_sequence_modify_my_topic.py` — placeholder test file
- `tests/expectations.py` — expected-output constants (for debug exercises)
- `tests/student_checker_support.py` — self-check support module

The agent then adds the exercise content to the notebooks. Your main job is to **review and refine** what the agent produces.

**Review the content** — Open both notebooks and check:

- The difficulty progression is appropriate for your class.
- The prompts are clear but do not give away the answer.
- The solution notebook provides correct, step-by-step solutions (not compact one-liners).
- The metadata tags (`exercise1`, `explanation1`, etc.) are preserved.

If something is not right, just tell the agent: *"Simplify the second task"*, *"Too much maths, focus on strings"*, or *"Add a worked example before exercise 3"*.

**Verify the notebook structure** — run the structural checks:

```bash
uv run python scripts/verify_exercise_quality.py \
  ex050_sequence_modify_my_topic --skip-empty-checks
```

The `--skip-empty-checks` flag is safe to use during notebook authoring — it allows the check to pass before the self-check module has been filled in. If you want more precise validation, add `--construct sequence --type modify`.

**What happens next (Phase 2 — tests)** — Once you are happy with the notebooks, tell the agent. The Exercise Test Creator agent will then write the pytest tests and the Exercise Test Reviewer will verify them. You do not need to write or run tests yourself.


## Exercise Reviewer — quick quality checks 🔍

The **Exercise Reviewer** is a review agent that checks newly-created exercises for pedagogical soundness, structure, and correct sequencing. It does **not** review tests — that is handled separately by the **Exercise Test Reviewer**.

The Exercise Generation agent runs the reviewer automatically as part of its workflow. You should not normally need to run it yourself, but you can if you want a quick check.

**How the review works (two passes):**

| Pass | When it runs | What it checks |
|------|-------------|----------------|
| **Pass 1** | After notebooks are written, before you review them | Exercise type is correct, concepts follow the right teaching order, tags and metadata are in place |
| **Pass 2** | After you approve the notebooks and supporting docs are generated | Teacher guidance files (README, OVERVIEW) are complete, solution quality is good, the exercise is listed in the teaching order |

**Output:** The reviewer returns a verdict: **PASS**, **PASS WITH NITS** (minor improvements), or **FAIL** (must fix), along with specific suggestions.

To run it manually from Copilot Chat, select **Exercise Reviewer** in the chat mode selector and ask: *"Review exercise ex050_sequence_modify_my_topic"*

**Tip:** Always use the exercise key (for example, `ex050_sequence_modify_my_topic`) — the reviewer finds exercises by key, not by file path.

## Best Practices

- **Be specific about exercise type** — The agent tailors the notebook format to the type you ask for:
  - **Debug**: Students fix broken code.
  - **Modify**: Students change working code to meet new requirements.
  - **Gap-Fill**: Students write missing lines inside a partially written program.
  - **Make**: Students write a solution from scratch.

  See the [exercise-type guides](../exercise-agents/exercise-types/) for detailed format rules.

- **Give teaching context, not just a title** — Instead of *"Write a loop exercise"*, tell the agent what students have covered recently and what they find difficult. The agent produces better content when it understands the classroom context.

- **Generate one set at a time** — Work through one exercise notebook fully before starting the next. This keeps each session focused and makes it easier to spot progression issues.

- **Fresh chat for each exercise** — Start a new chat for each exercise rather than continuing the same conversation. The agent works best with a clean context.

- **Review the agent's output** — The agent is helpful but not perfect. Read through the notebook, check that the difficulty is right for your class, and ask for adjustments before running the verification checks.
