# Creating and Editing Exercises

This guide covers how to create new exercises and tweak existing ones. Whether you're using the AI exercise generator or editing by hand, the key steps are the same: **branch, edit, verify, commit.**

- [Creating and Editing Exercises](#creating-and-editing-exercises)
  - [Before You Start: Branch First](#before-you-start-branch-first)
    - [How to create a branch (no command line needed)](#how-to-create-a-branch-no-command-line-needed)
  - [Creating New Exercises with the AI Assistant](#creating-new-exercises-with-the-ai-assistant)
    - [Quick steps](#quick-steps)
  - [Tweaking an Existing Exercise](#tweaking-an-existing-exercise)
    - [Finding the right files](#finding-the-right-files)
    - [What you can change](#what-you-can-change)
    - [A typical edit: fixing a typo in an instruction](#a-typical-edit-fixing-a-typo-in-an-instruction)
    - [Important: keep student and solution in sync](#important-keep-student-and-solution-in-sync)
  - [Verifying Your Changes](#verifying-your-changes)
    - [Quick check — one exercise](#quick-check--one-exercise)
    - [Full check — all exercises](#full-check--all-exercises)
    - [Quality check — structural and pedagogical](#quality-check--structural-and-pedagogical)
  - [Committing and Pushing](#committing-and-pushing)
    - [With VS Code (no command line)](#with-vs-code-no-command-line)
    - [Good commit messages](#good-commit-messages)
  - [Merging Your Branch Back](#merging-your-branch-back)
  - [Summary](#summary)

---

## Before You Start: Branch First

Before you make any changes, create a **branch**. A branch is like a separate copy of the files where you can experiment freely. The original stays untouched, so if something goes wrong, you can simply switch back.

### How to create a branch (no command line needed)

1. Click the branch name in the bottom-left corner of VS Code (it usually says **main**).
2. Select **Create new branch...** from the menu.
3. Give it a short name, like `edit-ex003` or `new-loops-exercise`.
4. Press Enter. You're now working on your new branch.

> **Why branch?** If you accidentally break an exercise, you can switch back to `main` and all your originals are safe. You can also have multiple changes in progress at once — a new exercise on one branch, a fix on another.

---

## Creating New Exercises with the AI Assistant

This repository includes a specialised Copilot assistant called the **Exercise Generation** agent that can create complete exercises (notebooks, solutions, and tests) from a short description.

### Quick steps

1. **Open Copilot Chat** — Click the Chat icon in the left sidebar (a speech bubble) or press `Ctrl+Alt+I` / `Cmd+Ctrl+I`.
2. **Select the Exercise Generation agent** — In the model selector at the top of the chat panel, choose **Exercise Generation**.
3. **Describe what you want** — For example:
   > "Create a set of modify exercises on string slicing for students who've just finished ex003."
4. **Review the suggestion** — The agent will describe what it plans to create. You can ask for changes (e.g., "Make the third task harder").
5. **Run the scaffold command** — The agent will tell you to run something like:

   ```bash
   uv run python scripts/new_exercise.py ex050 "String Slicing" \
     --construct sequence --type modify --slug string_slicing
   ```

   Copy and paste that into the **Terminal** (`Ctrl+`` `).
6. **Add the content** — The agent generates the notebook structure. Open both `student.ipynb` and `solution.ipynb` and paste in the exercise content the agent provided.
7. **Verify** — Run the quality check (see [Verifying Your Changes](#verifying-your-changes) below).

> **Full guide:** For a detailed walkthrough with examples and best practices, see [exercise-generation.md](exercise-generation.md).

---

## Tweaking an Existing Exercise

Sometimes you don't need a new exercise — you just want to adjust an existing one. Maybe a question is too hard, a typo slipped through, or you want to add a hint.

### Finding the right files

Exercises live in `exercises/<construct>/<exercise_key>/`. For example, the exercise `ex004_sequence_debug_syntax` lives in:

```text
exercises/sequence/ex004_sequence_debug_syntax/
├── exercise.json
├── notebooks/
│   ├── student.ipynb      ← The version students see
│   └── solution.ipynb      ← The completed version (for you)
└── tests/
    └── test_ex004_sequence_debug_syntax.py
```

### What you can change

| What to change | Where | Notes |
| --- | --- | --- |
| Instructions or scaffolding | `student.ipynb` (markdown cells) | Edit the text students read. |
| Code students start with | `student.ipynb` (code cells) | Change the starting code. |
| The solution | `solution.ipynb` | Keep this in sync with the student version. |
| The passing criteria | `tests/test_*.py` | Make the tests stricter or more lenient. |
| Exercise order or groupings | `repoman` command | This is handled when you create the template (see `how-to-use-the-template-repo-cli.md`). |

### A typical edit: fixing a typo in an instruction

1. Open `student.ipynb` in VS Code (double-click it in the file explorer).
2. Find the cell with the typo and edit it like a normal text document.
3. Open `solution.ipynb` and make the same edit there.
4. Run the tests to check everything still works (see below).

### Important: keep student and solution in sync

If you change an instruction in the student notebook, change it in the solution notebook too. If you change the starting code in the student notebook, update the solution to match. The tests run against the solution to confirm it passes — if the two notebooks drift apart, the solution will fail its own tests.

---

## Verifying Your Changes

After editing, always check that everything still works.

### Quick check — one exercise

```bash
uv run python scripts/run_pytest_variant.py --variant solution \
  exercises/sequence/ex004_sequence_debug_syntax/tests/test_ex004_sequence_debug_syntax.py -q
```

- Replace `ex004_sequence_debug_syntax` with your exercise key.
- If tests pass (green dots), your changes are good.
- If tests fail, read the error message — it tells you exactly what went wrong.

### Full check — all exercises

```bash
uv run ./scripts/verify_solutions.sh -q
```

This runs all solution tests for every exercise. It takes a bit longer but catches cross-exercise issues.

### Quality check — structural and pedagogical

```bash
uv run python scripts/verify_exercise_quality.py ex004_sequence_debug_syntax
```

This checks notebook structure, tags, and other non-test quality criteria.

---

## Committing and Pushing

Once your changes are verified, save them to GitHub.

### With VS Code (no command line)

1. Click the **Source Control** icon in the left sidebar (it looks like a branching tree).
2. Review the list of changed files. Each file shows what was added/removed.
3. Type a short message describing what you changed (e.g., "Fixed typo in ex004 instructions" or "Created new string slicing exercise").
4. Click the **Commit** button (✓).
5. Click **Publish Branch** or **Sync Changes** to upload to GitHub.

### Good commit messages

| Good | Less good |
| --- | --- |
| "Fixed typo in ex004 — missing closing quote" | "fix" |
| "Added new exercise: string slicing (ex050)" | "new stuff" |
| "Made exercise 3 easier — added hint about variables" | "updated" |

---

## Merging Your Branch Back

When you're happy with your changes and they've been committed and pushed, you can bring them back into the main branch.

1. On GitHub, navigate to your repository.
2. You'll see a banner saying "[branch name] had recent pushes" with a **Compare & pull request** button. Click it.
3. Review the changes summary.
4. Click **Create pull request**, then **Merge pull request**, then **Confirm merge**.
5. Back in VS Code, switch back to the `main` branch (click the branch name in the bottom-left, select `main`) and run **Pull** or **Sync** to get the merged version.

> **Can't see the banner?** Go to the **Pull requests** tab on GitHub and click **New pull request**. Set `main` as the base and your branch as the compare.

---

## Summary

1. **Branch first** — creates a safe sandbox.
2. **Make your changes** — use the AI agent or edit files directly.
3. **Verify** — run the tests.
4. **Commit** — save with a clear message.
5. **Push** — upload to GitHub.
6. **Merge** — bring changes back to main when you're done.

That's it. If something breaks, you can always switch back to `main` and start again.
