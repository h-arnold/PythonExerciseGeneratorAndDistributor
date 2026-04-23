# Generating Exercises with GitHub Copilot

This guide explains how to use the **Exercise Generation** assistant in GitHub Copilot to create new Python exercises for students. This tool is designed to help you quickly create pedagogically sound exercises without needing to manually write all the boilerplate code.

> Source of truth: execution, variant, and mapping contracts are defined in [docs/execution-model.md](execution-model.md).

## Repository status

New exercises scaffold directly into the canonical exercise directory. Canonical exercise identity and fail-fast contracts are defined in the execution model document, and flattened notebook/test mirrors are not part of the supported contract.

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
  - [Exercise Verifier — quick quality checks 🔍](#exercise-verifier--quick-quality-checks-)
    - [Recommended models — cost vs. quality 💡](#recommended-models--cost-vs-quality-)
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

This repository includes a specialized helper called the **Exercise Generation** agent. It knows how our grading system works and how to structure exercises for our students.

### 1. Select the Agent

In the Chat panel you just opened:

- Look for the model/agent selector (usually at the top or bottom of the chat window).
- Select **Exercise Generation** (you might see it in a dropdown list or by typing `@Exercise Generation`).
- *Note: If you don't see it, ensure you have the repository folder open as your workspace root.*

### 2. Crafting Your Prompt

The most important step is asking the right question. The agent works best when you give it **teaching context**.

Instead of asking "Write a loop exercise", explains what the students need to practice.

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

Once the agent gives you the exercise content (the "solution" code and the "student" instructions):

1. **Create the file structure**:

   Open the **Terminal** (`Ctrl + \`` or **Terminal > New Terminal**) and run the command the agent suggests inside the managed environment:

   ```bash
    uv run python scripts/new_exercise.py ex050 "My New Topic" \
      --construct sequence \
      --type modify \
      --slug my_topic
   ```

     The scaffolder writes directly to `exercises/sequence/ex050_sequence_modify_my_topic/` with `exercise.json`, `notebooks/student.ipynb`, `notebooks/solution.ipynb`, and `tests/test_ex050_sequence_modify_my_topic.py`. Do not move the scaffold after generation. Exercise type belongs in `exercise.json`, not in an extra path segment.

2. **Add the Content**:

    - Open both `exercises/sequence/ex050_sequence_modify_my_topic/notebooks/student.ipynb` and `exercises/sequence/ex050_sequence_modify_my_topic/notebooks/solution.ipynb`.
   - Keep the generated metadata tags (`exercise1`, `explanation1`, etc.) in place and shape the prompts/solutions following the patterns in [docs/exercise-types](exercise-types/).
   - Replace any placeholder `TODO`/`pass` code with the versions supplied by the agent (student copy in the main notebook, full answer in solutions).

3. **Verify**:

   Run the automated checks to confirm the notebooks and tests align:

   ```bash
    uv run python scripts/run_pytest_variant.py --variant solution \
      exercises/sequence/ex050_sequence_modify_my_topic/tests/test_ex050_sequence_modify_my_topic.py -q
   uv run python scripts/verify_exercise_quality.py \
     ex050_sequence_modify_my_topic
   ```

    The first command exercises the solution notebook; rerun it with `--variant student` once you expect the student notebook to pass as well.


## Exercise Verifier — quick quality checks 🔍

The **Exercise Verifier** is a companion verification agent that reviews newly-created or updated exercises against repository standards for canonical scaffold structure, metadata resolution, notebook tags/metadata, sequencing heuristics, and `OrderOfTeaching.md` coverage. It is typically invoked automatically as a sub-agent by the **Exercise Generation** agent, but you can also call it manually if you want an immediate verification.

How to run it manually:

- **From Copilot Chat**: Select the **Exercise Verifier** chatmode and ask something like:
  - "Verify exercise ex050_sequence_modify_my_topic" or
  - "Please verify exercise_key ex050_sequence_modify_my_topic"
- **Locally (command line)**:

  ```bash
  uv run python scripts/verify_exercise_quality.py \
    ex050_sequence_modify_my_topic
  ```

What it checks:

- Canonical scaffold structure and required file presence.
- Canonical metadata loading and resolver-based exercise discovery.
- Notebook tags, `metadata.language`, and debug explanation-cell structure.
- Construct progression heuristics and inclusion in `OrderOfTeaching.md`.
- It follows the rules in `docs/exercise-types/` and the verifier agent spec (`.github/agents/exercise_verifier.md.agent.md`).

Output:

- The verifier returns a concise verdict such as **OK: 0 warning(s)** or **FAIL: ...**, plus specific, minimal fixes (file(s) and suggestions).

**Tip:** Provide the canonical `exercise_key` (for example, `ex050_sequence_modify_my_topic`) when asking — the verifier now targets exercises by `exercise_key`, not by notebook path.

### Recommended models — cost vs. quality 💡

- **Raptor-mini (Preview)** — The best of the free models available in Copilot. It can produce good results but is sometimes inconsistent. The tests is generates are less good.  It is available with **50 free messages/month** on the free plan and **unlimited messages** for users with GitHub Education.

- **GPT 5.4** — This is the best of the current line of paid models. It's precise, follows instructions well and is particularly adept at generating tests that account for the ways in which students might bypass the required construct (e.g. using a while loop instead of a for loop) so that they are only told their solution is correct when it's correct in the intended way. It is available with the Copilot Education plan, which is free for students and teachers.

## Best Practices

- **Small Batches:** Generate one set of exercises at a time.
- **Fresh Context**: Start a new chat for each exercise for best results.
- **Be Specific about Type:**
  - **Debug**: Students fix broken code.
  - **Modify**: Students change working code.
  - **Make**: Students write from scratch.
  The agent knows the specific templates for these types.
