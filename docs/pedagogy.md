# **The Pedagogy Behind this Python Exercise Generator**

**TL;DR:** This project uses the **MDM (Modify, Debug, Make)** framework—a streamlined evolution of PRIMM designed for time-constrained, mixed-ability classrooms.

* **Schema Formation:** It prioritises high-volume exposure to code patterns over open-ended inquiry to build robust mental models.  
* **Low Friction:** By using **Jupyter Notebooks within GitHub Codespaces**, the setup eliminates technical friction and split-attention effects.  
* **Focus on Logic:** This allows students to focus entirely on rapid iteration, visual debugging, and understanding the logic rather than fighting the environment.

## **The Core Goals**

The pedagogical framework is driven by three specific objectives designed to counter the common points of failure in programming education.

### **1\. Robust Schema Formation (see MDM approach below)**

The primary learning objective is to build a mental model (schema) of code structures. When a student stares at a blank IDE cursor and freezes, it’s usually not because they don't "understand the logic"; it's because they lack the pattern-matching library that experienced developers take for granted.

To build this schema, students don't need to stare at one piece of code for 20 minutes; they need to see, touch, and break **lots** of code. We prioritise high-volume exposure to the same construct in slightly different contexts over abstract theory.

### **2\. Minimising Cognitive Load**

Cognitive Load Theory dictates that human working memory is limited. In a typical school setup, students are often forced to juggle a PDF worksheet, a separate IDE, and a browser. This "context switching" creates high *extraneous load*—mental effort wasted on managing windows rather than learning concepts.

MDM seeks to eliminate this. By keeping instructions, code, and output in a single vertical flow (Jupyter) and stripping back the IDE interface, we preserve the student's working memory for the actual coding task.

### **3\. Eliminating Classroom Friction**

Classroom momentum is fragile. In many programming lessons, the first 15 minutes are effectively lost to technical friction: managing local Python installations, missing libraries, or "it works on my machine" discrepancies.

This project aims for **zero-friction entry**. By using pre-baked cloud environments, we ensure every student starts with a working, identical setup the moment they click the link. The focus shifts entirely from "getting the environment to run" to "getting the code to work."

## **The MDM (Modify, Debug, Make) Approach**

This project is built around a specific pedagogical framework I've developed called **MDM (Modify, Debug, Make)**.

It is an evolution of the [PRIMM](https://teachcomputing.org/blog/using-primm-to-structure-programming-lessons/) approach, but aggressively adapted for the realities of the modern classroom—specifically, the constraints of limited curriculum time and the varying levels of digital resilience in a mixed-ability cohort.

### **The Problem with PRIMM (in Practice)**

We all love PRIMM (Predict, Run, Investigate, Modify, Make). It’s excellent theory. But in the trenches—with 30 students and 60 minutes a week—it often hits a wall.

* **The Time Crunch:** Doing the full PRIMM run takes time. In a short curriculum window, this often means students don't see enough *examples* to generalise the concept. They learn how *that specific loop* works, but they don't learn how *loops* work.  
* **Delayed Feedback Loop:** The predict and run phases are (rightly) highly important in PRIMM. However, for students who struggle to generalise, or find the whole concept quite overwhelming, the delay between the ‘predict’ and the ‘run’ and then importantly, using the run to refine their understanding takes too long and requires a lot of abstract thinking.

MDM takes the principles of PRIMM (purposeful thought and mental modelling) but shortens the feedback loop significantly.

## **The Framework**

### **1\. Modify: The Schema Builder**

This is the engine room of the framework. Instead of asking students to abstractly "Predict" what code will do, we ask them to "Modify" it to make it do something else.

This creates a rapid **Predict-Run-Feedback** cycle. To change the output, the student has to form a hypothesis (a mini-prediction), edit the syntax, and run it. If it fails, they get immediate feedback.

We don't do this once; we do it repeatedly. By exposing students to lots of permutations of the same construct, we build that mental model through repetition rather than abstract study.

**Example: Variable Assignment (Notebook Flow)**

*Instead of explaining memory allocation upfront, we use a gradient of difficulty within a Jupyter Notebook environment. The student interacts directly with live code cells.*

**Exercise 1: Targeted Substitution**

In this initial stage, the student runs the code to see the output, then receives a direct instruction to change a specific value (literal). They do not write new lines of code yet; they only edit existing data.

*Cell \[Markdown Instruction\]:*

**Exercise 1 — Change the greeting value**

**Task:** Set greeting \= "Hi there\!" so the output looks exactly like this:

Hi there\!

*Cell \[Code\]:*

```python
# Exercise 1 — YOUR CODE
# Modify the greeting assignment below
greeting = "Hello from Python!"
print(greeting)
```

**Exercise 10: Structural Expansion**

By the time students reach Exercise 10, they have modified variables enough times to understand the concept. Now, we ask them to combine multiple parts to form a coherent whole, testing their ability to manage multiple variables simultaneously.

*Cell \[Markdown Instruction\]:*

**Exercise 10 — Combine three parts**

**Task:** Assign new values so the print statement outputs Variables and strings make a message\!.

*Cell \[Code\]:*

```python
# Exercise 10 — YOUR CODE
# Assign new strings to each part to form a sentence
part_one = "Python"
part_two = "strings"
part_three = "matter"
print(part_one + " " + part_two + " " + part_three)
```

This progression is critical. It confirms: "Ah, the stuff in quotes is text I can change," (Exercise 1\) before demanding: "Now, coordinate these pieces to build a specific sentence" (Exercise 10).

**Replacing Inquiry with Explicit Exposure**

This phase effectively replaces the inquiry-based 'Investigate' model with a more explicit approach: "Here are all the different permutations of this concept."

Tech teachers and tech people alike are curious people who like to poke things to see how they work. It’s easy to assume that everyone is like this but it’s not always the case. Many students are terrified of breaking things, and plenty more aren’t interested enough in the subject to be curious. For them, open-ended investigation is just a source of anxiety.

MDM gives students who are struggling valuable time to see the different possibilities concretely, rather than having to try and imagine them in the abstract first. Curious students are, of course, free to experiment and investigate further, but the framework ensures that schema formation isn't dependent on a student's innate willingness to take risks.

### **2\. Debug: Building Resilience**

The vast majority of professional coding time is spent debugging. Unlike most other subjects, where students expect to have a go at something 2-3 times and then ‘get it’, in programming we always spend 80% of our time debugging, the only difference is the difficulty of the bugs\! MDM treats debugging as a primary skill to be taught explicitly.

By the time students reach this phase, the **Modify** tasks have given them a reasonable idea of what "good" code looks like. Now, we present them with "bad" code.

**Syntax Debugging: Inoculation**

We start by exposing students to common syntax errors—missing quotes, unclosed parentheses, typos—so they learn to recognise the error messages.

*From ex004\_debug\_syntax.ipynb:*

```python
# Exercise 6 — Store and print a message
# Expected output: Welcome to school

greeting = Welcome to school"
print(greeting
```

*Student Task:* Identify the missing opening quote and the missing closing parenthesis. This inoculates them against the panic of Seeing "SyntaxError".

**Logic Debugging: Tracing the Truth**

Once syntax is mastered, we move to code that *runs* perfectly but produces the wrong answer. This forces students to trace the logic step-by-step.

This is also a great opportunity to introduce the **debugger tool**. By modelling step-through debugging, we give students a live way to trace through how the code is *actually* running and visualise it (as opposed to how they *think* it is running). Watching variables change state line-by-line is often the breakthrough moment for determining what change needs to be made to get it working.

*From ex005\_debug\_logic.ipynb:*

```python
# Exercise 9 — Calculate perimeter
# Expected output: 30

length = 10
width = 5
perimeter = length + length + width
print(length)
```

*Student Task:* There are two errors here. First, the perimeter calculation is missing a side (+ width). Second, the print statement is outputting the length variable instead of the result (perimeter). Finding these requires reading the code, not just checking for red underlines.

Successfully completing these tasks builds resilience. It reframes the red text in the console from "You failed" to "Here is a puzzle to solve."

### **3\. Make: Fading the Scaffolding**

Only after Modify and Debug do we ask students to create from scratch. By now, the cognitive load of "what is the syntax?" has been reduced, allowing them to focus on "how do I solve the problem?"

I use a "faded scaffolding" approach here:

1. **Highly Scaffolded:** Tasks with natural language steps corresponding 1:1 with code lines.  
2. **Vague Briefs:** "Write a program that asks for a name and prints it backwards."

## **The Environment: Jupyter & VS Code**

The choice of using Jupyter Notebooks inside VS Code is a deliberate pedagogical decision, not just a preference for "cool tools."

### **1\. Zero-Friction Entry: GitHub Codespaces**

Pedagogy falls apart if the tool doesn't load. In a classroom, losing 15 minutes to "Miss, my Python isn't working" is fatal to the lesson's flow.

I use GitHub Codespaces to eliminate this friction entirely.

* **Pre-baked Environment:** The repository uses a custom **devcontainer** (built on Python 3.11) with all specific extensions and libraries pre-installed. We skip the lengthy "downloading docker image... running pip install..." phase. Students click a link, and they drop into a fully working environment.  
* **Curating the Interface:** VS Code is powerful, but that power creates visual noise. A standard install is cluttered with menus, sidebars, and pop-ups that distract novices. I use the devcontainer to inject strict VS Code settings presets that hide this complexity. By stripping away the UI clutter, we reduce the cognitive load, ensuring students are looking at their code, not getting lost in the IDE's settings menus.

### **2\. Eliminating Split Attention (Cognitive Load)**

In a traditional setup, a student has a worksheet (PDF/Paper) on one side and an IDE on the other. They are constantly switching contexts—reading an instruction, holding it in working memory, switching windows, and trying to type it out. This "context switching" carries a heavy cognitive tax known as the **Split Attention Effect**.

By using Jupyter Notebooks, the **instruction lives with the code**.

* The explanation of the concept is in a Markdown cell.  
* The code they need to modify is in the cell immediately below it.  
* The output appears immediately below that.

This proximity reduces the extraneous cognitive load, freeing up working memory for the actual task of understanding the logic.

### **3\. The Power of Cell-Based Debugging**

I chose VS Code specifically because of its robust integration with Jupyter, which allows for **step-through debugging of individual cells**.

Novice programmers often struggle because their mental model of execution differs from reality. They *think* the loop runs once more, or they *think* the variable updates before the condition check.

* **Visualisation:** The debugger allows them to see the code execute line-by-line. They watch variables update in real-time in the "Variables" pane.  
* **Industry Readiness:** A common complaint from industry professionals is that new graduates rely on print() statements and don't know how to use a debugger. By embedding this tool early in a friendly environment, we normalize its use.

This turns debugging from a guessing game into a scientific process: "I thought X would happen, but the debugger showed Y happened."

## **Why this works (The Theory)**

While MDM is my own synthesis, it is deeply informed by **Cognitive Load Theory**.

* **Reducing Extraneous Load:** By starting with working code (Modify), we remove the terror of the blank page. Students don't have to recall syntax *and* logic *and* structure all at once.  
* **Schema Acquisition:** The high volume of examples allows students to spot patterns (the invariants) across different contexts, building a more robust schema than a single deep-dive investigation usually permits.

This framework is "evidence-informed"—based on my observations of how students actually learn in a constrained environment, rather than how we wish they would learn in an ideal world.
