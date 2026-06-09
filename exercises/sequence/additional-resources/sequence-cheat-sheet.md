# Python Fundamentals: Sequence Cheat Sheet

### 1. Variables and Assignment

A **variable** is a named storage location in the computer’s memory used to hold data. Think of it as a labelled box where you can store a value to use later.
**Assignment** is the process of putting data into that variable using the equals sign (`=`).

**Worked Example:**

```python
# We assign the value "Bassaleg" to the variable named 'school_name'
school_name = "Bassaleg"

# We assign the value 9 to the variable named 'year_group'
year_group = 9
```

### 2. The Four Core Data Types

When we store data in a variable, the computer needs to know what *type* of data it is. This dictates what operations we can perform on it.

| **Data Type** | **Description** | **Example in Python** | 
| :--- | :--- | :--- |
| **String** | Text, characters, or symbols. Always wrapped in speech marks (`""` or `''`). | `"Computer Science"`, `"1234"` | 
| **Integer** | A whole number, positive or negative. No decimal point. | `14`, `-5`, `0` | 
| **Float** | A fractional number containing a decimal point. | `3.14`, `9.99`, `-0.5` | 
| **Boolean** | A logical value that can only be one of two states: True or False. (Note the capital letters in Python). | `True`, `False` | 

**Worked Example:**

```python
is_raining = True        # Boolean
temperature = 14.5       # Float
number_of_pupils = 30    # Integer
lesson_topic = "Python"  # String
```

### 3. Input (Getting Data from the User)

A program often needs to ask the user for information. We use the `input()` function to pause the program and wait for the user to type something.
To make sure the user knows what to type, we use a `print()` statement on the line above to ask the question.

*Crucial Rule: Any data grabbed using `input()` is automatically stored as a **String**, even if the user types a number!*

**Worked Example:**

```python
# Step 1: Print the question to the screen
print("What is your favourite subject?")

# Step 2: Wait for the user to type, then store it in a variable
subject = input()

# Now we can use the variable
print("You chose:")
print(subject)
```

### 4. Simple Mathematical Operators

Just like in a maths lesson, we can perform calculations in Python. We use specific symbols, called **operators**, to do this.

* `+` : Addition
* `-` : Subtraction
* `*` : Multiplication (Asterisk)
* `/` : Division (Forward slash)

**Worked Example:**

```python
# Calculating the total cost of items
item_one = 5
item_two = 10

total = item_one + item_two
print(total)  # Outputs: 15

# Calculating an average
average = total / 2
print(average) # Outputs: 7.5
```

### 5. Casting (Data Type Conversion)

Sometimes a program needs a value to be a different data type. **Casting** allows you to convert data from one type to another. This is especially useful when we want to do maths with numbers we got from an `input()`.

* `str()`: Converts a value into a String.
* `int()`: Converts a value into an Integer.
* `float()`: Converts a value into a Float.

**Worked Example:**

```python
# The user types "25", which is currently a String (text)
print("How old are you?")
user_input = input() 

# We cast the string into an integer so we can do maths with it
age = int(user_input) 

new_age = age + 1
print(new_age) 
```

### 6. Concatenation (Joining Strings)

**Concatenation** is the technical term for joining two or more strings (text) together to make one longer string. We use the addition symbol (`+`) to achieve this.

*Crucial Rule: You can only concatenate strings with other strings. If you want to join a string and a number, you must **cast** the number to a string first!*

**Worked Example:**

```python
first_name = "Alan "
last_name = "Turing"

# Concatenating two strings
full_name = first_name + last_name 
print(full_name) # Outputs: Alan Turing

# Concatenating a string and an integer (Requires Casting!)
birth_year = 1912
message = full_name + " was born in " + str(birth_year) + "."

print(message) # Outputs: Alan Turing was born in 1912.
```