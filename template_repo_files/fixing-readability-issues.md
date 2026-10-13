# Making your Python easier to read

When you run a notebook self-check, it checks both what your code does and a set
of readability rules. A task is complete only when its functional checks **and**
its readability check pass. Readability failures are required fixes, not optional
tips. Work through the individual results in the table; there is no overall summary.

Save your notebook before checking. The **Exercise** number identifies the task;
its **Readability** row refers to that task's code. Findings include a rule
code such as `E225` and the **line** and **column** within that cell (both start at
1). Long messages continue on extra table lines; they are not shortened or cut off.
Edit the saved cell, save again, and run the self-check again. Fix each reported
readability issue. A clean readability result does not prove that code works,
that names are meaningful, or that comments are useful. Teacher-side marks are
unchanged by these checks.

## Code index

| Rule | What it helps with |
| --- | --- |
| [E101](#e101) | Mixing tabs and spaces |
| [E111](#e111) | Indentation not in four-space multiples |
| [E117](#e117) | Extra indentation |
| [E225](#e225) | Spaces around assignment and comparison |
| [E226](#e226) | Spaces around arithmetic |
| [E227](#e227) | Spaces around bitwise and shift operators (later topic) |
| [E228](#e228) | Spaces around modulo |
| [E231](#e231) | Spaces after punctuation |
| [E501](#e501) | Long lines |
| [E741](#e741) | Ambiguous one-letter names |
| [N802](#n802) | Function names (later topic) |
| [N803](#n803) | Function arguments (later topic) |
| [N806](#n806) | Variables inside functions (later topic) |
| [N816](#n816) | Mixed-case names outside functions |
| [W191](#w191) | Tabs used for indentation |
| [W291](#w291) | Spaces at the end of a line |
| [W293](#w293) | Spaces on an otherwise blank line |

The examples are small demonstrations, not answers to your exercise. In the
whitespace examples, `<TAB>` stands for one actual tab character and `<SPACE>`
stands for one actual space. The markers themselves are not Python syntax.

<a id="e101"></a>
### E101 — Do not mix tabs and spaces in indentation

Use spaces consistently. A tab can look different in different editors, so
mixing it with spaces makes the block hard to judge.

**Non-example**
```python
if True:
<SPACE><SPACE><TAB>print("hello")
<SPACE><SPACE><TAB>print("again")
```

**Corrected example**
```python
if True:
    print("hello")
    print("again")
```
Both lines inside the block now use spaces. This example still parses; when
indentation breaks Python syntax completely, see [Syntax errors](#syntax-errors).

<a id="e111"></a>
### E111 — Indent in four-space multiples

Each step into a block should add four spaces. This makes the shape of your code
easy to see.

**Non-example**
```python
if True:
  print("hello")
```

**Corrected example**
```python
if True:
    print("hello")
```
The block now starts four spaces in, rather than two.

<a id="e117"></a>
### E117 — Do not indent a block too far

Indent a line by one four-space step for each block it is inside. Extra spaces
can make a line look as if it belongs to a different block.

**Non-example**
```python
if True:
        print("hello")
```

**Corrected example**
```python
if True:
    print("hello")
```
The line now has one indentation step for its one `if` block.

<a id="e225"></a>
### E225 — Put spaces around `=` and comparisons

Spaces around assignment (`=`) and comparison operators make the two sides
easier to read.

**Non-example**
```python
score=3
if score==3:
    print("yes")
```

**Corrected example**
```python
score = 3
if score == 3:
    print("yes")
```
The spaces separate the names and values from the operators.

<a id="e226"></a>
### E226 — Put spaces around arithmetic operators

Spaces around arithmetic such as `+` and `*` make a calculation easier to scan.

**Non-example**
```python
total=score+2
```

**Corrected example**
```python
total = score + 2
```
The assignment and addition are now visually separate.

<a id="e227"></a>
### E227 — Put spaces around bitwise and shift operators (later topic)

Bitwise operators such as `&` and shift operators such as `<<` are later-topic
Python. This rule does not mean you need to use them in an introductory task.

**Non-example**
```python
flags=left&right
```

**Corrected example**
```python
flags = left & right
```
Spaces make the operator and its two values distinct.

<a id="e228"></a>
### E228 — Put spaces around modulo

Modulo (`%`) gives the remainder after division. Add spaces around it as you
would around other arithmetic operators.

**Non-example**
```python
remainder=number%2
```

**Corrected example**
```python
remainder = number % 2
```
The spaces make the calculation easier to follow.

<a id="e231"></a>
### E231 — Add a space after punctuation

When a comma separates items, put a space after it. This makes the items easier
to tell apart.

**Non-example**
```python
colours = ["red","blue"]
```

**Corrected example**
```python
colours = ["red", "blue"]
```
There is now a space after the comma.

<a id="e501"></a>
### E501 — Keep lines to a readable length

This check uses a 100-character limit, but Ruff has exceptions: for example,
some long strings, URLs and comment-like lines are not reported. A line that
passes this check is not automatically easy to understand.

**Non-example**
```python
message = "This is a deliberately long message that keeps going so the line crosses the one hundred character limit used by this readability check."
```

**Corrected example**
```python
message = (
    "This is a deliberately long message that keeps going so the line crosses "
    "the one hundred character limit used by this readability check."
)
```
Splitting the string across lines makes the source easier to view while keeping
the same message.

<a id="e741"></a>
### E741 — Avoid names that look like other characters

The lowercase letter `l` can look like the number `1`, while `O` can look like
zero and `I` like a capital i. Choose a clearer name.

**Non-example**
```python
l = 4
print(l)
```

**Corrected example**
```python
count = 4
print(count)
```
The name `count` gives a reader more information and is not easily confused.

<a id="n802"></a>
### N802 — Use lowercase function names (later topic)

Functions are a later topic. When you write one, use lowercase words separated
by underscores, called `snake_case`.

**Non-example**
```python
def ShowScore():
    print("score")
```

**Corrected example**
```python
def show_score():
    print("score")
```
The function name now uses lowercase words separated by an underscore.

<a id="n803"></a>
### N803 — Use lowercase function arguments (later topic)

Function arguments are names supplied to a function, so this is also a
later-topic rule. Write them in lowercase with underscores between words.

**Non-example**
```python
def show_score(PlayerName):
    print(PlayerName)
```

**Corrected example**
```python
def show_score(player_name):
    print(player_name)
```
Both the argument and its use have been updated to the same lowercase name.

<a id="n806"></a>
### N806 — Use lowercase local variables (later topic)

A local variable is created inside a function. Functions and their local
variables are later topics; use lowercase `snake_case` names for those variables.

**Non-example**
```python
def show_score():
    PlayerScore = 3
    print(PlayerScore)
```

**Corrected example**
```python
def show_score():
    player_score = 3
    print(player_score)
```
The variable and its use now have the same lowercase name.

<a id="n816"></a>
### N816 — Use lowercase names outside functions

For ordinary names outside functions, use lowercase words separated by
underscores. Python constants are often written in capitals; Ruff permits those.

**Non-example**
```python
playerScore = 3
```

**Corrected example**
```python
player_score = 3
```
Changing the name to `snake_case` makes its word boundary clear. An uppercase
constant such as `MAX_SCORE` remains allowed by this rule.

<a id="w191"></a>
### W191 — Use spaces, not tabs, for indentation

A tab is one tab character even if your editor displays it as several spaces.
Use four space characters for one indentation step.

**Non-example**
```python
if True:
<TAB>print("hello")
```

**Corrected example**
```python
if True:
    print("hello")
```
The visible `<TAB>` marker above represents an actual tab; the corrected line
starts with four actual spaces.

<a id="w291"></a>
### W291 — Remove spaces at the end of a line

Trailing whitespace means spaces or tabs after the last visible character.
Here `<SPACE>` represents one actual space after the closing parenthesis.

**Non-example**
```python
print("hello")<SPACE>
```

**Corrected example**
```python
print("hello")
```
The corrected line ends immediately after the closing parenthesis.

<a id="w293"></a>
### W293 — Keep blank lines empty

A blank line should contain no spaces or tabs. Here `<SPACE>` represents one
actual space on an otherwise blank line.

**Non-example**
```python
score = 3
<SPACE>
print(score)
```

**Corrected example**
```python
score = 3

print(score)
```
The line between the statements is now truly empty, rather than containing a
space character.

## Syntax errors

Ruff must understand the Python before it can check all readability rules. For
example, this inconsistent indentation cannot be parsed:

```python
if True:
    print("inside")
  print("unclear")
```

That is different from the E101 example above: its tab-and-space indentation
mix is inconsistent style, but that example parses and can receive an E101
readability finding. A syntax error blocks a complete readability assessment
for its cell. Its readability row shows **⚪ NOT CHECKED** with the message
“Not checked - make sure your code runs first” instead of a list of syntax
diagnostics. This is not a readability pass. Fix the syntax error first, save,
then check again. Other cells are still checked. Code with valid syntax receives
readability feedback even if its functional checks fail.

## If the tool reports an error

If the self-check says the Ruff tool failed, ask your teacher for help. Do not
install packages yourself or suppress or remove a check to hide the error. If an
exercise instruction requires an identifier that conflicts with a naming result,
keep the required identifier and ask your teacher; do not silently waive the
result.

## A note for teachers and reference solutions

Existing reference solutions may receive readability failures even when their
functional checks pass. That does not mean their code is functionally wrong.
The future correction pass is separate; these checks do not change teacher-side
marks in this implementation.

Ruff checks only part of the WJEC naming expectations. Lowercase and mixed-case
rules do not judge whether a name is meaningful, and permitted uppercase
constants are not rejected. E111 checks indentation in multiples of four; it
does not impose a separate rule for every block depth. E501 follows Ruff's
exceptions rather than counting every character in every line.

The checker runs in the native Python environment used by supported Jupyter,
GitHub Codespaces and the supplied VS Code Dev Container setups. A browser-only
Pyodide runtime is not promised. Readability results are required for the
self-check, but teacher-side marks remain based on the existing functional tests.
