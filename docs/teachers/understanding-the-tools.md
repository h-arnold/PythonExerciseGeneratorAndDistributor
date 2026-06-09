# Understanding the Tools — A Teacher's Overview

This guide explains the key tools this project uses and how they fit together. You don't need to be a developer to use them — think of this as a plain-English map of the landscape.

- [Understanding the Tools — A Teacher's Overview](#understanding-the-tools--a-teachers-overview)
  - [GitHub](#github)
  - [GitHub Repositories](#github-repositories)
  - [GitHub Classroom](#github-classroom)
  - [GitHub Codespaces](#github-codespaces)
  - [Version Control (Git)](#version-control-git)
    - [Committing changes](#committing-changes)
    - [Pushing changes](#pushing-changes)
    - [Pulling the latest version](#pulling-the-latest-version)
    - [Branches and pull requests (for bigger changes)](#branches-and-pull-requests-for-bigger-changes)
    - [Good habits to teach students](#good-habits-to-teach-students)
  - [Jupyter Notebooks](#jupyter-notebooks)
  - [How It All Fits Together](#how-it-all-fits-together)

---

## GitHub

GitHub is a website that stores code online. Think of it like Google Drive for programming projects — it keeps everything backed up, tracks changes over time, and lets people work together.

In this project, you'll use GitHub for two things:

- **Storing your exercises** — this repository (`PythonExerciseGeneratorAndDistributor`) is where you create, edit, and organise exercises.
- **Distributing work to students** — you'll push a copy of selected exercises to a new repository, then use GitHub Classroom to give each student their own copy.

> **What you need:** A free GitHub account. If your school uses GitHub, you may already have one. Sign up at [github.com](https://github.com).

---

## GitHub Repositories

A **repository** (or "repo") is a project folder on GitHub. It contains all the files for that project, plus a history of every change ever made.

There are three types of repo involved in this workflow:

| Type | What it's for |
| --- | --- |
| **Source repo** | Where you author and edit exercises (this repo: `PythonExerciseGeneratorAndDistributor`). |
| **Template repo** | A packaged subset of exercises, created by the `repoman` tool, ready to use in Classroom. |
| **Student repos** | Individual copies that GitHub Classroom creates when students accept an assignment. Each student gets their own. |

---

## GitHub Classroom

GitHub Classroom is a free tool that helps you manage coding assignments. When you create an assignment and point it at a template repository, Classroom:

1. Creates a **copy of the template for each student** who accepts.
2. Links those copies to your Classroom roster so you can track submissions.
3. (Optional) Runs **autograding tests** when students push their work, showing results in the Classroom dashboard.

**You don't need to install anything.** Classroom runs in your browser at [classroom.github.com](https://classroom.github.com).

> **Getting started:** You'll need to authorise Classroom to access your GitHub account (or your school's GitHub organisation). Follow the on-screen prompts — it takes about two minutes.

---

## GitHub Codespaces

Codespaces gives every student a **ready-to-go coding environment in their browser**. No installation, no "it works on my machine," no IT department requests.

**Why this matters for your classroom:**

- **No local setup.** Students don't install Python, Jupyter, or anything else. Everything runs in the cloud.
- **Works on any device** — Chromebooks, tablets, school laptops — as long as there's a browser and internet connection.
- **Pre-configured.** The environment comes with the right extensions, settings, and files already in place. Students open it and start coding.
- **Isolated.** Each student's workspace is separate. Nobody's setup affects anyone else's.
- **Free.** All users get 50 hours free Codespaces usage per month. Getting a free GitHub Education licence get 150 hours free usage for students and teachers.

---

## Version Control (Git)

Git is the system that tracks every change to a file. It is built into GitHub and runs automatically in the background. When you **commit** and **push** work, Git records a snapshot of the project at that moment — like taking a photo of your work and saving it to the cloud.

### Committing changes

When you have finished editing an exercise and want to save your progress:

1. In VS Code, click the **Source Control** icon in the left sidebar (it looks like a branching tree). You will see a list of every file you have changed.
2. Review the list to make sure you are not accidentally including something unfinished.
3. At the top of the Source Control panel, type a short message describing what you changed — for example, *"Added ex050 (modify: string concatenation)"* or *"Fixed typo in ex003 solution"*.
4. Click the **Commit** button (✓). This saves a snapshot of your changes on your computer.

Committing is like saving a file — the change is recorded, but only on your machine so far.

### Pushing changes

To back your work up to GitHub (and make it available to others):

1. After committing, click **Sync Changes** or the **Push** button in the Source Control panel.
2. VS Code uploads your commits to GitHub.

Now your changes are backed up. If your computer breaks, or you switch to another machine, your work is still there.

> **Tip:** Push regularly — at least at the end of each session. There is no downside, and it means you never lose progress.

### Pulling the latest version

Before starting a new session, it is good practice to **pull** the latest version from GitHub — especially if you or a colleague may have made changes from another computer.

Open a terminal (**Terminal > New Terminal**) and run:

```bash
git pull
```

Or use the **Source Control** panel menu (the **...** icon) and select **Pull**.

### Branches and pull requests (for bigger changes)

When you are making significant edits — especially ones you are unsure about — it is safest to work on a **branch**. A branch is like a separate copy of the project. Your changes live on the branch and do not affect the main version until you are ready.

**Creating a branch:**

1. Click the branch name in the bottom-left corner of VS Code (it will say **main** by default).
2. Select **Create new branch...** and give it a name, such as *add-ex050* or *simplify-ex008*.
3. Make your changes, commit them, and push as normal — they go to your new branch, not to main.

**Opening a pull request (PR):**

Once you have pushed your branch, you can open a pull request to merge your changes into main:

1. Open the **Source Control** panel, click the **...** menu, and select **Push** (if you have not already).
2. VS Code may show a prompt offering to create a pull request on GitHub — follow the prompts. This opens a page in your browser.
3. On the GitHub page, add a title and description explaining what you changed, then submit the pull request.
4. Review the changes on GitHub and click **Merge pull request** when you are ready.

After merging, switch back to the **main** branch in VS Code and run **git pull** to get the merged version.

**Why use branches and pull requests?**

- **Safety:** The original work stays untouched until you explicitly merge.
- **History:** Every pull request is recorded, so you can look back at what changed and why.
- **Revert:** If a change turns out to be a mistake, you can undo the entire pull request in one click.

### Good habits to teach students

| Habit | Why |
| --- | --- |
| **Commit after finishing an exercise.** | Creates a save point they can return to. |
| **Write a short, meaningful message.** | "Finished exercise 3" is useful. "Update" is not. |
| **Push regularly.** | Gets work backed up to GitHub (and triggers autograding if set up). |
| **Pull before starting.** | Makes sure they have the latest version (useful if you push updates mid-assignment). |

---

## Jupyter Notebooks

Jupyter Notebooks (`.ipynb` files) are documents that mix **instructions** and **code** in one file. Commonly used in data science to combine explanations, code, and results, they work well for teaching programming too.

```text
┌─────────────────────────────────┐
│  Exercise 1 — Change the        │  ← Markdown cell (instructions)
│  greeting value                 │
├─────────────────────────────────┤
│  greeting = "Hello!"            │  ← Code cell (student writes here)
│  print(greeting)                │
├─────────────────────────────────┤
│  Hello!                         │  ← Output (appears when they run it)
└─────────────────────────────────┘
```

**Why notebooks work well for teaching:**

- **Instructions sit right above the code.** No switching between a worksheet and an editor. This reduces cognitive load.
- **Students run code inline.** Click a cell, press `Shift+Enter`, and see the result immediately.
- **You can hide complexity.** Each exercise is its own cell — students focus on one small task at a time.
- **Autograding targets specific cells.** The grading system knows which cells are which exercises and checks them independently.

---

## How It All Fits Together

Here's the complete flow, from your desk to your students' screens:

```text
  YOU                               GITHUB                         STUDENTS
 ─────────────────────────────────────────────────────────────────────────

  1. Create exercises in          Source repo                      
     the source repo           (PythonExerciseGenerator            
                               AndDistributor)                     
         │                                                         
  2. Run repoman ──►  Creates a template repo ──►        
                               on GitHub                           
                                                                    
  3. Create Classroom           Assignment linked                  
     assignment                  to template repo                  
         │                                                         
  4. Students accept                                         Each gets their own
     assignment                                               copy of the repo
                                                              ↓
  5. Students open                                      Codespace opens in
     in Codespaces                                       their browser
                                                              ↓
  6. Students complete                                   They edit notebook
     exercises                                           cells and run them
                                                              ↓
  7. Students commit                                     Work saved to their
     and push                                            GitHub repo
                                                              ↓
  8. (Optional)                                         Results appear in
     Autograding runs                                    Classroom dashboard
```

**In short:** You create and organise exercises in the source repo. You package them into a template. Classroom hands copies to students. Students work in Codespaces. Git tracks everything. Autograding (currently broken) reports back.