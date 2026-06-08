# Getting Started — Your First Exercise Set

This tutorial walks you through the complete workflow: from understanding the tools, to packaging exercises, to distributing them in GitHub Classroom. Follow the steps in order — each one builds on the last.

- [Getting Started — Your First Exercise Set](#getting-started--your-first-exercise-set)
  - [The big picture](#the-big-picture)
  - [Step 1: Understand the tools](#step-1-understand-the-tools)
  - [Step 2: Open this repository in GitHub Codespaces](#step-2-open-this-repository-in-github-codespaces)
  - [Step 3: Authenticate with GitHub](#step-3-authenticate-with-github)
  - [Step 4: Create a template repository](#step-4-create-a-template-repository)
    - [Before moving on](#before-moving-on)
  - [Step 5: Create a GitHub Classroom assignment](#step-5-create-a-github-classroom-assignment)
    - [5.1 Go to GitHub Classroom](#51-go-to-github-classroom)
    - [5.2 Create a new assignment](#52-create-a-new-assignment)
    - [5.3 Link your template repository](#53-link-your-template-repository)
    - [5.4 (Optional) Set up autograding](#54-optional-set-up-autograding)
    - [5.5 Share the invite link](#55-share-the-invite-link)
  - [Step 6: Students complete the exercises](#step-6-students-complete-the-exercises)
    - [6.1 Open in Codespaces](#61-open-in-codespaces)
    - [6.2 Work through the exercises](#62-work-through-the-exercises)
    - [6.3 Check progress with the self-checker](#63-check-progress-with-the-self-checker)
    - [6.4 Save and submit work](#64-save-and-submit-work)
    - [6.5 What you'll see as a teacher](#65-what-youll-see-as-a-teacher)
  - [Step 7: Create or tweak exercises](#step-7-create-or-tweak-exercises)
  - [What next?](#what-next)

---

## The big picture

Here's what you'll end up with by the end of this tutorial:

```text
Your source repo ──► Template repo ──► Classroom assignment ──► Student copies
(PythonExercise      (packaged set      (you create this,     (each student
 GeneratorAnd         of exercises)      students accept)      gets their own)
 Distributor)
```

You only need a browser and a GitHub account. No installation, no IT department (usually).

> **Note:** Some schools block GitHub and WebSocket connections, which are required for GitHub Codespaces. If that's the case at your school, speak to your IT team — you can share this document with them that explains exactly what needs unblocking and why it's safe: [IT Network Requirements](it-network-requirements.md).

---

## Step 1: Understand the tools

Before you start, read the overview of the key concepts:

> **[Understanding the Tools](understanding-the-tools.md)** — a plain-English guide to GitHub, GitHub Classroom, Codespaces, version control, and Jupyter notebooks.

It takes about 10 minutes and explains how all the pieces fit together. You can come back to it later as a reference.

**When you're done, return here and move to Step 2.**

--
## Step 2: Open this repository in GitHub Codespaces

1. Open [this page, which is the root of the repository](https://github.com/h-arnold/PythonExerciseGeneratorAndDistributor) in your browser.

2. Click the green **Code** button, select the **Codespaces** tab, then click **Create codespace on main**.

![A screenshot of the 'Create new Codespace' button.](docs/images/open-in-codespaces.png)

3. Wait a few minutes for the Codespace to build. Once it's built, you should have a working VSCode instance in the browser.

> 💡**Tip:** Sign up for a GitHub Education account (free) to get 100 extra free hours of CodeSpaces usage. 
> [Sign up here](https://github.com/education) 

---

## Step 3: Authenticate with GitHub

To create template repositories, the command-line tool needs permission to access your GitHub account. You need to do this once per session.

1. Open the **Terminal** in VS Code (`Ctrl + `` ` or **Terminal > New Terminal** from the menu).
2. Run these two commands, one at a time:

   ```bash
   unset GITHUB_TOKEN
   gh auth login
   ```

3. Follow the on-screen prompts (choose **Login with a browser** if asked, then enter the code shown in the terminal on the GitHub website).

> **Why two commands?** Codespaces starts with a temporary token that only has permission for this repository. The first command clears it. The second lets you sign in with your full GitHub account so the tool can create repositories on your behalf.

---

## Step 4: Create a template repository

Now you'll bundle some exercises into a template repository — a ready-to-use package that GitHub Classroom can distribute to students.

Run this in the **Terminal**:

```bash
template_repo_cli create --construct sequence --repo-name my-first-exercises
```

This takes all the exercises from the `sequence` topic and creates a new public template repository called `my-first-exercises` on your GitHub account.

**What if I want different exercises?**

```bash
# Only modify exercises
template_repo_cli create --construct sequence --type modify --repo-name sequence-modify

# Specific exercises by key
template_repo_cli create \
  --exercise-keys ex002_sequence_modify_basics ex003_sequence_modify_variables \
  --repo-name getting-started

# Exercises from multiple topics
template_repo_cli create \
  --construct sequence selection \
  --type modify \
  --repo-name week1-python \
  --name "Week 1: Sequence and Selection"
```

### Before moving on

Check the repository exists on GitHub:

1. Go to [github.com](https://github.com) and log in.
2. You should see `my-first-exercises` (or whatever you named it) in your repositories list.
3. Click into it — you should see the notebooks and test files inside.

> **Trouble?** See the full guide at [How to Use the Template Repo CLI](how-to-use-the-template-repo-cli.md), or run `template_repo_cli create --help`.

---

## Step 5: Create a GitHub Classroom assignment

> ⚠️ **Note:** GitHub Classroom is being sunsetted by GitHub. This workflow will work for at least the next year and will be updated with its FOSS replacement when it's ready.

Now you'll turn your template repository into a classroom assignment.

### 5.1 Go to GitHub Classroom

1. Open [classroom.github.com](https://classroom.github.com) in your browser.
2. Sign in with your GitHub account (the same one you used in Step 3).
3. If you haven't used Classroom before, you'll be asked to authorise it — click **Authorise GitHub Classroom**.
4. You'll see a list of your classrooms. If you don't have one yet, click **Create a classroom** and choose your GitHub organisation (or your personal account).

### 5.2 Create a new assignment

1. Inside your classroom, click the **Assignments** tab, then **Create assignment**.
2. Give it a title — for example, "Week 1: Getting Started with Python".
3. (Optional) Set a deadline. Students can still submit after the deadline, but late work is marked clearly.
4. Choose **Individual assignment** or **Group assignment** — most programming exercises use individual.

### 5.3 Link your template repository

1. Under **Repository**, choose **Import a repository from GitHub**.
2. Click **Connect GitHub account** and select the organisation or account where you created the template.
3. Search for `my-first-exercises` (or whatever you named it) and select it.
4. Leave the rest of the settings at their defaults — they're already configured for this project.

### 5.4 (Optional) Set up autograding

If you want tests to run automatically when students push their work:

1. Scroll down to **Add autograding test**.
2. Click **Add test** and choose **Run python**.
3. In the **Test command** field, enter:

   ```bash
   pytest
   ```

4. Click **Save test case**.

> Without autograding, students still get feedback from the self-checker cell in each notebook. Autograding just reports results back to your Classroom dashboard.

### 5.5 Share the invite link

1. Click **Create assignment** at the bottom.
2. Classroom will show you an **invite link** — something like `https://classroom.github.com/a/AbCdEfGh`.
3. Share this link with your students (email, your school's VLE, or however you normally communicate).
4. When students click it and accept, GitHub Classroom creates a personal copy of the template repository for each of them. They'll see:

   ```text
   my-school/my-first-exercises-student1
   my-school/my-first-exercises-student2
   my-school/my-first-exercises-student3
   ...
   ```

**That's it — your first assignment is live.**

---

## Step 6: Students complete the exercises

Now that students have accepted the assignment and have their own copies, here's what their workflow looks like.

### 6.1 Open in Codespaces

Each student's assignment repository has a green **Code** button. They click it, select **Codespaces**, then **Create Codespace**.

> 💡**Tell students to start their Codespace at the beginning of the lesson**, not when you say "open your work." By the time you're ready to teach, their environment will be ready.

### 6.2 Work through the exercises

The exercises are Jupyter notebooks — each cell is one small task:

1. **Read the instruction** (the text above the code cell).
2. **Run the code cell** (`Shift+Enter` or click the play button).
3. **Edit the code** as instructed.
4. **Run it again** to check the output.
5. **Move to the next cell.**

Students can run cells as many times as they like. Nothing breaks.

### 6.3 Check progress with the self-checker

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

> **Encourage students to run the self-checker after every exercise**, not just at the end. They catch mistakes sooner.

### 6.4 Save and submit work

At the end of each lesson (or after finishing an exercise), students should:

1. Click the **Source Control** icon in the left sidebar (branch icon).
2. Type a short message (e.g., "Finished exercises 1 and 2").
3. Click **Commit** (✓), then **Sync Changes** to push to GitHub.

This backs up their work and, if you enabled autograding in Step 5, triggers the tests and reports results to your Classroom dashboard.

### 6.5 What you'll see as a teacher

- **After each push**: if autograding is set up, Classroom shows pass/fail results per student in the assignment dashboard.
- **At a glance**: you can see who's attempted which exercises, who's stuck, and who's finished.
- **Without autograding**: the self-checker still gives students feedback — you just won't see the results in the dashboard. You can ask students to run it and show you, or check their notebooks directly.

> **Detailed classroom tips:** See [Classroom Practices](classroom-practices.md) for start-of-lesson routines, troubleshooting common issues, and building good git habits.

---

## Step 7: Create or tweak exercises

Now that you know the distribution workflow, you can start creating your own exercises or adjusting the ones already in the repository.

> **[Creating and Editing Exercises](creating-and-editing-exercises.md)** — learn how to use the AI exercise generation assistant, edit existing notebooks by hand, verify your changes, and commit/push safely.

Key points from that guide:

- **Branch first** — create a branch before editing, so you can always revert.
- **Use the Exercise Generation agent** — describe what you want in Copilot Chat, and it creates the notebook structure for you.
- **Always verify** — run the solution tests to check your changes work.
- **Commit and push** — save your work to GitHub with a clear message.

---

## What next?

| If you want to... | Read this |
| --- | --- |
| Run lessons smoothly | [Classroom Practices](classroom-practices.md) — start-of-lesson routines, self-checker, git habits, troubleshooting |
| Understand the pedagogy | [Pedagogy](pedagogy.md) — why the Modify-Debug-Make framework works |
| Create exercises in detail | [Exercise Generation with Copilot](exercise-generation.md) — full reference for the AI assistant |
| Explore all CLI options | [Template Repo CLI reference](../developers/template_repo_cli.md) — every flag and option |
