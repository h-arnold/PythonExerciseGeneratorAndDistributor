# Exercise Testing Conventions (GitHub Classroom Python Runner)

These conventions align our pytest suites with the stock GitHub Classroom Python autograder runner (version 3 results). They enable predictable grouping, scoring, and reporting without custom plugins.

## Core rules

- **Use @pytest.mark.task(taskno=N)** on every test for exercise N. This drives grouping and ordering in the runner output.
- **Do not use subTest**. Convert subtests to parametrized pytest cases so they are visible at collection time and counted predictably.
- **Prefer parametrization for variants**. Each param case becomes its own collected test item (and its own score slice).
- **Multiple tests per exercise are allowed**. Keep the same taskno across related tests; use descriptive test names for clarity.
- **Scoring model (stock runner)**: max-score is divided equally among all collected test items (including parametrized cases). Passing items get their share; failing/error get 0. No per-exercise weights.

## Writing tests for an exercise

- **Simple exercises**: One test function with multiple assertions is acceptable, but a failing assertion stops later checks. Use this when atomicity is acceptable.
- **Finer-grain feedback/partial credit**: Split into multiple test functions or parametrized cases, all tagged with the same taskno for that exercise.
- **Naming**: The runner trims class names and test_and replaces underscores with spaces. Descriptive names still help maintainers (e.g. test_ex002_strings_basic, test_ex002_strings_edge_cases).

### Converting subtests to parametrization (example)

```python
import pytest

# Before (subtests – avoid)
def test_greeter_subtests():
    for name in ["Ada", "Bob"]:
        with subtests.test(name=name):
            assert greet(name) == f"Hello, {name}!"

# After (parametrized – preferred)
@pytest.mark.parametrize("name", ["Ada", "Bob"])
@pytest.mark.task(taskno=2)
def test_greeter(name):
    assert greet(name) == f"Hello, {name}!"
```

## Computing max-score automatically (without subtests)

When you avoid subTest, the collected item count is stable. You can derive max-score in CI and feed it to the autograder action:

```yaml
- name: Count pytest items
  id: count
  run: |
    COUNT=$(pytest --collect-only -q 2>/dev/null | grep -E '::' | wc -l)
    echo "max_score=$COUNT" >> "$GITHUB_OUTPUT"

- name: Python autograder
  uses: classroom-resources/autograding-python-grader@v1
  with:
    max-score: ${{ steps.count.outputs.max_score }}
    timeout: 15
    setup-command: 'pip install -r requirements.txt'
```

Notes:

- Parametrized cases are counted; ensure parametrization reflects intended granularity.
- If you ever reintroduce subTest, the runtime may produce more test entries than the pre-count; avoid subTest to keep scoring consistent.

## Checklist per exercise

- [ ] Tag every test with @pytest.mark.task(taskno=<exercise_number>).
- [ ] Use parametrization for variants; avoid subTest.
- [ ] Decide granularity (single test vs multiple/parametrized) to match desired feedback and scoring slices.
- [ ] Keep failure messages clear; they surface in Classroom.
- [ ] If CI computes max-score, ensure no subTest usage so counts stay accurate.
