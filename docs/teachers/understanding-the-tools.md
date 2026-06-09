# Understanding the Tools — A Teacher's Overview

This guide explains the key tools this project uses and how they fit together. You don't need to be a developer to use them — think of this as a plain-English map of the landscape.

- [Understanding the Tools — A Teacher's Overview](#understanding-the-tools--a-teachers-overview)
  - [GitHub](#github)
  - [GitHub Repositories](#github-repositories)
  - [GitHub Classroom](#github-classroom)
  - [GitHub Codespaces](#github-codespaces)
  - [Version Control (Git)](#version-control-git)
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

Git is the system that tracks every change to a file. It's built into GitHub and runs automatically in the background. When you or your students **commit** and **push** work, Git records a snapshot of the project at that moment.

**Good habits to teach students:**

| Habit | Why |
| --- | --- |
| **Commit after finishing an exercise.** | Creates a save point they can return to. |
| **Write a short, meaningful message.** | "Finished exercise 3" is useful. "Update" is not. |
| **Push regularly.** | Gets work backed up to GitHub (and triggers autograding if set up). |
| **Pull before starting.** | Makes sure they have the latest version (useful if you push updates mid-assignment). |

**For you as a teacher:**

- Commit and push your changes to the source repo regularly.
- Before making big edits to an exercise, create a **branch** — that way the original stays intact and you can revert if something breaks.
- The Source Control tab in VS Code (the branch icon in the left sidebar) handles all of this without needing the command line.

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