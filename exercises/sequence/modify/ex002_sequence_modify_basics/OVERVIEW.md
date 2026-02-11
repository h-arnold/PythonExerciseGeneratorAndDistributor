# Exercise ex002: Sequence Modification Basics - Overview

## Summary
Created a 10-part **modification** exercise set for absolute beginners learning Python sequence (sequential execution).

## Key Features

- **No variables** - only literals and operators
- Topics covered:
  - Basic print statements
  - String output
  - Simple arithmetic (+, -, *, /)
  - String concatenation
- **Modification exercises**: Students modify working code to meet new requirements
- Difficulty progression: starts with single-word changes, builds to multi-element modifications

## Files Created

- **Notebook**: [notebooks/ex002_sequence_modify_basics.ipynb](notebooks/ex002_sequence_modify_basics.ipynb)
  - 10 exercises with tagged cells (`exercise1` through `exercise10`)
  - Clear instructions and expected output for each
  - Self-check cell for experimentation

- **Tests**: [tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py](tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py)
  - 40 test cases total (3-4 per exercise)
  - Captures stdout to verify print output
  - Smoke tests verify all cells execute
  - Behavioral tests verify correct modifications

- **Exercise folder**: [exercises/sequence/modify/ex002_sequence_modify_basics/](exercises/sequence/modify/ex002_sequence_modify_basics/)
  - README.md with student/teacher notes
  - Properly placed in `sequence/modify/` hierarchy

## Test Status
✅ All 10 exercise cells execute without errors
❌ 24/40 behavioral tests fail (expected - students haven't modified code yet)

This is the correct behavior for modification exercises:

- Students start with working code
- Tests verify the modified (correct) output
- Until students make modifications, most tests will fail

## Exercise Progression

1. **Ex 1-2**: Simple word substitution in print statements
2. **Ex 3**: Change arithmetic operator (+ to *)
3. **Ex 4**: String concatenation with 3 parts
4. **Ex 5**: Arithmetic operator change with division
5. **Ex 6**: Multiple print statements (3 lines)
6. **Ex 7**: Concatenation with numbers as strings
7. **Ex 8**: Multi-number arithmetic
8. **Ex 9**: Combining text and calculation (2 prints)
9. **Ex 10**: Complex concatenation (5 parts)

## Pedagogical Notes

- Designed for students aged 14-18 in their first Python lesson
- Inverted order: modification before debugging (as requested)
- No advanced features (no input(), no functions, no variables)
- Each exercise has clear expected output
- Students learn by changing working code, not writing from scratch

## Usage
Students:

1. Open `notebooks/ex002_sequence_modify_basics.ipynb`
2. Read each exercise description
3. Modify the code in tagged cells
4. Run cells to see output
5. Run `pytest tests/ex002_sequence_modify_basics/test_ex002_sequence_modify_basics.py` to verify

Teachers:

- Reference solutions in [notebooks/solutions/ex002_sequence_modify_basics.ipynb](notebooks/solutions/ex002_sequence_modify_basics.ipynb)
- Tests are deterministic and fast (< 1s total)
- Can be used with GitHub Classroom autograding
