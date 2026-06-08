# Classroom Practices — Tips for Running Lessons

This guide covers the day-to-day habits that make lessons run smoothly, from starting Codespaces to using the self-checker and handling common hiccups.

- [Classroom Practices — Tips for Running Lessons](#classroom-practices--tips-for-running-lessons)
  - [Start of Lesson: Fire Up Codespaces First](#start-of-lesson-fire-up-codespaces-first)
  - [Working Through Exercises](#working-through-exercises)
  - [Using the Self-Checker Cell](#using-the-self-checker-cell)
  - [Encouraging Good Git Habits](#encouraging-good-git-habits)
  - [When Things Go Wrong](#when-things-go-wrong)
  - [End of Lesson: Commit and Push](#end-of-lesson-commit-and-push)

---

## Start of Lesson: Fire Up Codespaces First

Codespaces can take up to 5 minutes to build. Therefore:

> **Tell students to open their Codespace as soon as they log in, not when you say "open your work."**

This simple habit saves 5–10 minutes of dead time per lesson. Here's the routine:

1. Students log into [github.com](https://github.com).
2. They navigate to their assignment repository (it will be named something like `my-school/assignment-name-student123`).
3. They click the green **Code** button and select **Open in Codespaces**.
4. (First time only) They click **Create Codespace** — subsequent times they can click the existing Codespace name.
5. The browser loads VS Code with the notebook editor ready.

While that loads, you can take the register, recap the previous lesson, or hand out starter activities. By the time you're ready to start, their environment is ready.

> **Tip:** Bookmark the GitHub Classroom assignment page, or give students a short link to their repo. The fewer steps they have to remember, the better.

---

## Working Through Exercises

Each exercise notebook is organised into cells. Students work through them top to bottom.

**The typical flow for one exercise part:**

1. **Read the instruction** (the text above the code cell).
2. **Run the code cell** by clicking it and pressing `Shift+Enter` (or clicking the play button that appears when you hover over it).
3. **See what happens** — the output appears below the cell.
4. **Edit the code** as instructed.
5. **Run it again** to check the output matches what's expected.
6. **Move to the next cell.**

**Point out to students:**

- They can run a cell as many times as they like. It won't "break" anything.
- If they get stuck, the instruction cell usually gives a hint about what to change.
- The code in earlier cells stays available — variables they set in cell 1 can be used in cell 2 (unless a cell explicitly resets things).

---

## Using the Self-Checker Cell

At the bottom of each exercise notebook, there is a **self-checker cell**. This is a special cell that students run to see how they're doing.

**How to use it:**

1. Scroll to the last cell in the notebook (it will be labelled something like "Check your work").
2. Run it with `Shift+Enter`.
3. Read the results table.

**What the results mean:**

```text
┌────────────────────────────────────────────┐
│  Test                 Result   Feedback    │
├────────────────────────────────────────────┤
│  Exercise 1: greeting  ✅ Pass  Well done! │
│  Exercise 2: message   ❌ Fail  Expected   │
│                        output to contain   │
│                        "Hello", got "Hi"   │
│  Exercise 3: loop      ⚠️ Not  Did you     │
│                        run    complete this │
│                        this?  exercise?    │
└────────────────────────────────────────────┘
```

- **✅ Pass** — That exercise is correct.
- **❌ Fail** — Something is wrong. Read the feedback to see what the test expected vs. what it got.
- **⚠️ Not run this?** — The checker couldn't find work for that exercise. Either it hasn't been attempted yet, or the cell tag is missing.

**Why the self-checker is useful:**

- Students get **immediate feedback** without waiting for you to mark their work.
- The feedback is **specific** — it tells them what went wrong, not just "try again."
- It encourages **self-assessment** — students can check their own work before moving on.

> **Encourage students to run the self-checker after every exercise**, not just at the end. That way they catch mistakes early.

---

## Encouraging Good Git Habits

Git tracks every change students make. The key actions are:

| Action | What it does | When to do it |
| --- | --- | --- |
| **Commit** | Saves a snapshot of their current work. | After finishing each exercise (or at the end of the lesson). |
| **Push** | Uploads commits to GitHub (and triggers autograding if enabled). | At the end of every lesson (or when they want to submit). |
| **Pull** | Downloads the latest version from GitHub. | At the start of a new lesson (in case you pushed updates). |

**How to commit and push (no command line needed):**

1. Click the **Source Control** icon in the left sidebar (it looks like a branching tree).
2. You'll see a list of changed files. Hover over them to see what changed.
3. Type a short message in the text box at the top (e.g., "Finished exercise 1 and 2").
4. Click the **Commit** button (✓).
5. Click the **Sync Changes** button (or **Push**) to upload to GitHub.

**What to tell students:**

- "Commit when you finish an exercise — it's like saving a checkpoint in a game."
- "Write a message that tells Future You what you did. 'Finished exercise 3' is good. 'stuff' is not."
- "Push at the end of every lesson so your work is backed up."
- "If your computer crashes, all your committed work is safe on GitHub."

---

## When Things Go Wrong

Most issues are quick to fix. Here are the common ones:

| Problem | Likely cause | What to try |
| --- | --- | --- |
| **Codespace won't start** | Browser or network issue. | Refresh the page. If it still won't start, try a different browser or check your internet. |
| **Codespace timed out / stopped** | Inactivity timeout (30 min by default). | Click **Start** or **Resume** — your files are still there. |
| **"Kernel not found" or "No kernel"** | The Python kernel hasn't started yet. | Click the **Select Kernel** button (top-right of the notebook) and pick the recommended option (usually "Python 3.11" or "Python Environments"). If there's only one option, select it. |
| **Code runs but output looks wrong** | A logic error in the student's code. | Read the instruction again. Check variable names and values. Run the self-checker for specific feedback. |
| **Self-checker shows "Not run" for a completed exercise** | The cell tag might be missing or the code wasn't saved. | Make sure the cell actually contains code. Run it once, then re-run the checker. |
| **Can't push — "permission denied"** | The Codespace token expired or isn't authorised. | Close and reopen the Codespace. If it persists, have the student check they're the owner of the repo. |

**If you're stuck:**

- The notebook self-checker feedback is the best place to start — it usually tells you exactly what's wrong.
- Check that the student ran the cell containing their answer (not just read it).
- Ask: "Did it work before? What changed between then and now?" — this often isolates the problem.

---

## End of Lesson: Commit and Push

Make this the last 2-3 minutes of every lesson. Build the habit:

1. **Commit** — "Commit all changes with a message like 'End of lesson 3 work'."
2. **Push** — Click Sync Changes to upload.
3. **Stop the Codespace** — Close the tab, or stop it from the Codespaces dashboard at [github.com/codespaces](https://github.com/codespaces). This frees up usage time.

> **Why stop the Codespace?** Codespaces has a monthly usage limit (free tier includes 60 hours). Stopping unused Codespaces saves those hours for when students are actually working.
