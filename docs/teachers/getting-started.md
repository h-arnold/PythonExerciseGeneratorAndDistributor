# Getting Started — Your First Exercise Set

This guide shows you the fastest way to get Python exercises into your students' hands using pre-built template repositories. You only need a browser and a GitHub account — no installation, no command line, no exercise creation.

- [Getting Started — Your First Exercise Set](#getting-started--your-first-exercise-set)
  - [The big picture](#the-big-picture)
  - [Step 1: Understand the tools](#step-1-understand-the-tools)
  - [Step 2: Pick a template repository](#step-2-pick-a-template-repository)
  - [Step 3: Create a GitHub Classroom assignment](#step-3-create-a-github-classroom-assignment)
    - [3.1 Go to GitHub Classroom](#31-go-to-github-classroom)
    - [3.2 Create a new assignment](#32-create-a-new-assignment)
    - [3.3 Link your template repository](#33-link-your-template-repository)
    - [3.4 (Optional) Set up autograding](#34-optional-set-up-autograding)
    - [3.5 Share the invite link](#35-share-the-invite-link)
  - [Step 4: Students complete the exercises](#step-4-students-complete-the-exercises)
    - [4.1 Open in Codespaces](#41-open-in-codespaces)
    - [4.2 Work through the exercises](#42-work-through-the-exercises)
    - [4.3 Check progress with the self-checker](#43-check-progress-with-the-self-checker)
    - [4.4 Save and submit work](#44-save-and-submit-work)
    - [4.5 What you'll see as a teacher](#45-what-youll-see-as-a-teacher)
  - [What next?](#what-next)

---

## The big picture

Here's what you'll end up with by the end of this tutorial:

```text
Existing template repo ──► Classroom assignment ──► Student copies
(already built and       (you create this,        (each student
 ready to use)            students accept)         gets their own)
```

> **ℹ️ Note:** Some schools block GitHub and WebSocket connections, which are required for GitHub Codespaces. If that's the case at your school, speak to your IT team — you can share this document with them that explains exactly what needs unblocking and why it's safe: [IT Network Requirements](it-network-requirements.md).

---

## Step 1: Understand the tools

Before you start, read the overview of the key concepts:

> **[Understanding the Tools](understanding-the-tools.md)** — a plain-English guide to GitHub, GitHub Classroom, Codespaces, version control, and Jupyter notebooks.

It takes about 10 minutes and explains how all the pieces fit together. You can come back to it later as a reference.

**When you're done, return here and move to Step 2.**

---

## Step 2: Pick a template repository

The **[Construct Template Repositories](construct-template-repos.md)** page lists every pre-built template repository available in this project. Each one bundles all the exercises for a topic — for example, `sequence` or `selection` — and is ready to use in GitHub Classroom.

Browse the table, then choose the template repo that matches what you want to teach this week. Here's a quick example:

| Construct | Template Repository |
|-----------|-------------------|
| `sequence` | `python-exercises-sequence` |
| `selection` | `python-exercises-selection` |

> **🛠️ Can't find the combination you need?** See [Creating Custom Exercise Sets](creating-exercise-sets.md) for how to build your own template repos or create new exercises.

---

## Step 3: Create a GitHub Classroom assignment

> **ℹ️ Note:** GitHub Classroom is being sunsetted by GitHub. This workflow will work for at least the next year and will be updated with its FOSS replacement when it's ready.

Now you'll turn your chosen template repository into a classroom assignment.

### 3.1 Go to GitHub Classroom

1. Open [classroom.github.com](https://classroom.github.com) in your browser.
2. Sign in with your GitHub account.
3. If you haven't used Classroom before, you'll be asked to authorise it — click **Authorise GitHub Classroom**.
4. You'll see a list of your classrooms. If you don't have one yet, click **Create a classroom** and choose your GitHub organisation (or your personal account).

### 3.2 Create a new assignment

1. Inside your classroom, click the **Assignments** tab, then **Create assignment**.
2. Give it a title — for example, "Week 1: Getting Started with Python".
3. (Optional) Set a deadline. Students can still submit after the deadline, but late work is marked clearly.
4. Choose **Individual assignment** or **Group assignment** — most programming exercises use individual.

### 3.3 Link your template repository

1. Under **Repository**, choose **Import a repository from GitHub**.
2. Click **Connect GitHub account** and select the account where the template repo lives.
3. Search for the template repo you picked in Step 2 (for example, `python-exercises-sequence`) and select it.
4. Leave the rest of the settings at their defaults — they're already configured for this project.

### 3.4 (Optional) Set up autograding

If you want tests to run automatically when students push their work:

1. Scroll down to **Add autograding test**.
2. Click **Add test** and choose **Run python**.
3. In the **Test command** field, enter:

   ```bash
   pytest
   ```

4. Click **Save test case**.

> Without autograding, students still get feedback from the self-checker cell in each notebook. Autograding just reports results back to your Classroom dashboard.

### 3.5 Share the invite link

1. Click **Create assignment** at the bottom.
2. Classroom will show you an **invite link** — something like `https://classroom.github.com/a/AbCdEfGh`.
3. Share this link with your students (email, your school's VLE, or however you normally communicate).
4. When students click it and accept, GitHub Classroom creates a personal copy of the template repository for each of them. They'll see:

   ```text
   my-school/python-exercises-sequence-student1
   my-school/python-exercises-sequence-student2
   my-school/python-exercises-sequence-student3
   ...
   ```

**That's it — your first assignment is live.**

---

## Step 4: Students complete the exercises

Now that students have accepted the assignment and have their own copies, here's what their workflow looks like.

### 4.1 Open in Codespaces

Each student's assignment repository has a green **Code** button. They click it, select **Codespaces**, then **Create Codespace**.

> **👩‍🏫 Tell students to start their Codespace at the beginning of the lesson**, not when you say "open your work." By the time you're ready to teach, their environment will be ready.

### 4.2 Work through the exercises

The exercises are Jupyter notebooks — each cell is one small task:

1. **Read the instruction** (the text above the code cell).
2. **Run the code cell** (`Shift+Enter` or click the play button).
3. **Edit the code** as instructed.
4. **Run it again** to check the output.
5. **Move to the next cell.**

Students can run cells as many times as they like. Nothing breaks.

### 4.3 Check progress with the self-checker

At the bottom of each notebook is a **self-checker cell**. Running it shows a table:

```text
┌────────────────────────────────────────────┐
│  Test                 Result   Feedback    │
├────────────────────────────────────────────┤
│  Exercise 1: greeting  ✅ Pass  Well done! │
│  Exercise 2: message   ❌ Fail  Expected   │
│                        output to contain   │
│                        "Hello", got "Hi"   │
```

Students get immediate, specific feedback on each exercise without waiting for you to mark their work.

> **👩‍🏫 Encourage students to run the self-checker after every exercise**, not just at the end. They catch mistakes sooner.

### 4.4 Save and submit work

At the end of each lesson (or after finishing an exercise), students should:

1. Click the **Source Control** icon in the left sidebar (branch icon).
2. Type a short message (e.g., "Finished exercises 1 and 2").
3. Click **Commit** (✓), then **Sync Changes** to push to GitHub.

This backs up their work and, if you enabled autograding in Step 3, triggers the tests and reports results to your Classroom dashboard.

### 4.5 What you'll see as a teacher

- **After each push**: if autograding is set up, Classroom shows pass/fail results per student in the assignment dashboard.
- **At a glance**: you can see who's attempted which exercises, who's stuck, and who's finished.
- **Without autograding**: the self-checker still gives students feedback — you just won't see the results in the dashboard. You can ask students to run it and show you, or check their notebooks directly.

> **📖 Detailed classroom tips:** See [Classroom Practices](classroom-practices.md) for start-of-lesson routines, troubleshooting common issues, and building good git habits.

---

## What next?

| If you want to... | Read this |
| --- | --- |
| Build custom exercise sets with the `repoman` CLI | [Creating Custom Exercise Sets](creating-exercise-sets.md) — full walkthrough including Codespaces, authentication, and the repoman tool |
| Understand the tools in more depth | [Understanding the Tools](understanding-the-tools.md) |
| Run lessons smoothly | [Classroom Practices](classroom-practices.md) — start-of-lesson routines, self-checker, git habits, troubleshooting |
| Understand the pedagogy | [Pedagogy](pedagogy.md) — why the Modify-Debug-Make framework works |
| Create brand-new exercises | [Creating and Editing Exercises](creating-and-editing-exercises.md) — with the AI assistant or by hand |
