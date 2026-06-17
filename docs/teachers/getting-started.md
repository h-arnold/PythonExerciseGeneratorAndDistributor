# Getting Started — Your First Exercise Set

This guide shows you the fastest way to get Python exercises into your students' hands using pre-built template repositories. You only need a browser and a GitHub account — no installation, no command line, no exercise creation.

- [Getting Started — Your First Exercise Set](#getting-started--your-first-exercise-set)
  - [The big picture](#the-big-picture)
  - [Prerequisites](#prerequisites)
  - [Step 1: Understand the tools](#step-1-understand-the-tools)
  - [Step 2: Pick a template repository](#step-2-pick-a-template-repository)
  - [Step 3: Create a GitHub Classroom assignment](#step-3-create-a-github-classroom-assignment)
    - [3.1 Create a new GitHub Classroom](#31-create-a-new-github-classroom)
    - [3.2 Create a new assignment](#32-create-a-new-assignment)
    - [3.3 Link your template repository](#33-link-your-template-repository)
    - [3.4 Creating your assignment](#34-creating-your-assignment)
    - [3.5 Share the invite link](#35-share-the-invite-link)
    - [3.6 What the students need to do](#36-what-the-students-need-to-do)
  - [What next?](#what-next)

---

## The big picture

Here's what you'll end up with by the end of this tutorial:

```text
Existing template repo ──► Classroom assignment ──► Student copies
(already built and       (you create this,        (each student
 ready to use)            students accept)         gets their own)
```

## Prerequisites

- Access to Github and Github Codespaces. Some schools block these by so check with your IT team if you have trouble accessing them. More information here: [IT Network Requirements](it-network-requirements.md)
- A GitHub account. If you don't have one, sign up at [github.com](github.com).

> Tip: Sign up to [GitHub Education](https://github.com/education) to get extra Codespaces hours (50 on free, 150 on GitHub Education), amongst other benefits.

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

> **🛠️ Can't find the combination you need?** See [Creating Custom Exercise Sets](creating-exercise-sets.md) for how to build your own template repos or create new exercises.

---

## Step 3: Create a GitHub Classroom assignment

> **ℹ️ Note:** GitHub Classroom is being sunsetted by GitHub. This workflow will work for at least the next year and will be updated with its FOSS replacement when it's ready.

Now you'll turn your chosen template repository into a classroom assignment.

### 3.1 Create a new GitHub Classroom

1. Open [classroom.github.com](https://classroom.github.com) in your browser.
2. Sign in with your GitHub account.
3. If you haven't used Classroom before, you'll be asked to authorise it — click **Authorise GitHub Classroom**.
4. Click **New classroom** and follow the instructions to create one.

### 3.2 Create a new assignment

1. Inside your classroom, click the **Assignments** tab, then **New assignment**.
2. Give it a title — for example, "Week 1: Getting Started with Python".
3. (Optional) Set a deadline. Students can still submit after the deadline, but late work is marked clearly.
4. Choose **Individual assignment** or **Group assignment** — most programming exercises use individual.
5. Click **Continue**.

### 3.3 Link your template repository

1. Under **Find a Github repository**, enter one of the template repository names you picked in Step 2 (for example, `h-arnold/python-exercises-sequence`) and select it.

<figure>
  <img src="../images/choosing-a-template-repo.png" alt="Selecting a Template Repository on GitHub Classroom">
  <figcaption>Selecting a Template Repository on GitHub Classroom</figcaption>
</figure>

2. **Optional but recommended**: set **Repository visibility** to **Private**. This keeps students from seeing each other's work. Leave **Give students admin access to their repository** unchecked. This prevents students from accidentally deleting their work.
3. On **Add a supported editor**, select **Codespaces**.

<figure>
  <img src="../images/selecting-code-spaces-on-github-classroom-assignment.png" alt="Selecting GitHub Codespaces on the 'Add a supported editor' screen">
  <figcaption>Selecting GitHub Codespaces on the 'Add a supported editor' screen</figcaption>
</figure>
4. Click **Continue** to move to the next step.

### 3.4 Creating your assignment

This will take you to the **Set up autograding and feedback** page. You can skip this step — it gets set up automatically for you anyway.

1. Scroll to the bottom of the page and click **Create assignment**.

### 3.5 Share the invite link

This will take you to the Github Classroom Assignment page that you just created.

1. Copy the invite link:
  
<figure>
  <img src="../images/github-classroom-invite-link.png" alt="The GitHub Classroom invite link">
  <figcaption>The GitHub Classroom invite link</figcaption>
</figure>

2. Share this link with your students in the normal way (e.g. on MS Teams or Google Classroom).

### 3.6 What the students need to do

1. They need to click on the link you gave them. This will invite them to the assignment and if they haven't joined the classroom already, accepting this assignment will add them to the GitHub Classroom.
2. They need to click 'Accept this assignment'.
3. They need to click the **Open in Codespaces** button to start their Codespace. 

> Tip: Opening codespaces will take a few minutes to get started the first time, so tell students to do this at the start of the lesson, not when you say "open your work." By the time you're ready to teach, their environment will be ready.

---

## Ready to teach?

Your assignment is live and students have accepted the invite. The next guide covers everything that happens in the classroom — from opening exercises to submitting work:

> **[In the Classroom — Running Exercises with Students](in-the-classroom.md)**

That guide covers:
- Choosing and opening exercises
- Selecting the Python kernel (a common stumbling block)
- Running code and using the self-checker
- Saving and submitting work
- What you'll see as a teacher

---

## What next?

| If you want to... | Read this |
| --- | --- |
| Build custom exercise sets with the `repoman` CLI | [Creating Custom Exercise Sets](creating-exercise-sets.md) — full walkthrough including Codespaces, authentication, and the repoman tool |
| Guide students through exercises | [In the Classroom](in-the-classroom.md) — student workflow: opening notebooks, running code, self-checker, submitting |
| Understand the tools in more depth | [Understanding the Tools](understanding-the-tools.md) |
| Run lessons smoothly | [Classroom Practices](classroom-practices.md) — start-of-lesson routines, self-checker, git habits, troubleshooting |
| Understand the pedagogy | [Pedagogy](pedagogy.md) — why the Modify-Debug-Make framework works |
| Create brand-new exercises | [Creating and Editing Exercises](creating-and-editing-exercises.md) — with the AI assistant or by hand |
