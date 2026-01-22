# Implementation Plan: Per-Exercise Weighted Scoring System

**Date:** 2026-01-22  
**Objective:** Implement a pytest-based weighted scoring system that allows parametrized tests to contribute proportionally to exercise-specific point allocations, with GitHub Classroom integration.

**Reference:** GitHub Classroom autograding-python-grader  
https://github.com/classroom-resources/autograding-python-grader

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [GitHub Classroom Integration Model](#github-classroom-integration-model)
4. [Files to Create](#files-to-create)
5. [Files to Modify](#files-to-modify)
6. [Detailed Component Specifications](#detailed-component-specifications)
7. [Integration Points](#integration-points)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Steps](#deployment-steps)
10. [Example Output](#example-output)
11. [Appendices](#appendices)

---

## Overview

### Current State

- **Tests exist** for 5 exercises (ex001-ex005) with parametrized tests
- **No scoring system** - pytest only reports pass/fail counts
- **No GitHub Classroom integration** - no autograding configuration
- **Test framework** - Custom `notebook_grader.py` for executing tagged cells

### Target State

- **Exercise-weighted scoring** - each exercise has a configurable point value
- **Parametrized tests contribute proportionally** - 8/10 tests passed → 80% of exercise points
- **Detailed feedback** - students see which exercises they struggled with
- **GitHub Classroom ready** - outputs scores in compatible format
- **Backward compatible** - existing tests work without modification

### Design Principles

1. **Zero test modifications** - existing tests work as-is
2. **Configuration-driven** - weights defined in JSON, not code
3. **Transparent feedback** - clear breakdown of scoring per exercise
4. **Maintainable** - single plugin file, minimal complexity
5. **Standards-compliant** - follows pytest plugin architecture

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     pytest Execution Flow                        │
├─────────────────────────────────────────────────────────────────┤
│  1. pytest loads scoring_plugin.py via pytest.ini               │
│  2. pytest_configure() registers ExerciseScoringPlugin          │
│  3. pytest collects all test items                              │
│  4. pytest_collection_modifyitems() tags each test with         │
│     exercise name (extracted from test file path)               │
│  5. Tests execute normally (no changes to test behavior)        │
│  6. pytest_runtest_logreport() records pass/fail for each       │
│     test, grouped by exercise                                    │
│  7. pytest_sessionfinish() calculates weighted scores:          │
│     - Per exercise: (passed/total) × weight                     │
│     - Total: sum of all exercise scores                         │
│  8. Write test-results.json in GitHub Classroom format         │
│  9. Print detailed breakdown to console                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            test-results.json (GitHub Classroom Format)          │
├─────────────────────────────────────────────────────────────────┤
│  {                                                               │
│    "version": 3,                                                │
│    "status": "pass",  // or "fail" or "error"                  │
│    "tests": [                                                    │
│      {                                                           │
│        "name": "ex001_sanity",                                  │
│        "status": "pass",                                        │
│        "score": 5.0,                                            │
│        "max_score": 5.0,                                        │
│        "output": "4/4 tests passed"                            │
│      },                                                          │
│      {                                                           │
│        "name": "ex002_sequence_modify_basics",                 │
│        "status": "fail",                                        │
│        "score": 12.0,                                           │
│        "max_score": 15.0,                                       │
│        "output": "8/10 tests passed"                           │
│      }                                                           │
│    ]                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              GitHub Actions Workflow                            │
├─────────────────────────────────────────────────────────────────┤
│  1. Run: pytest (plugin executes automatically)                │
│  2. Plugin writes test-results.json                            │
│  3. Workflow reads JSON and outputs to $GITHUB_OUTPUT          │
│  4. GitHub Classroom consumes score via autograding action     │
└─────────────────────────────────────────────────────────────────┘
```

---

## GitHub Classroom Integration Model

### autograding-python-grader Output Format

Based on the [autograding-python-grader](https://github.com/classroom-resources/autograding-python-grader) repository, the expected JSON format is:

```python
# From runner/data.py in autograding-python-grader
{
  "version": 3,                    # Integer: format version
  "status": "pass",                # String: "pass", "fail", or "error"
  "message": null,                 # Optional[String]: error message if status="error"
  "tests": [                       # List[Test]: individual test results
    {
      "name": "exercise name",     # String: human-readable test name
      "status": "pass",            # String: "pass", "fail", or "error"
      "message": null,             # Optional[String]: failure/error message
      "test_code": "",             # String: test source code (optional)
      "output": "",                # Optional[String]: captured stdout
      "score": 12.0,               # Float: points earned for this test
      "max_score": 15.0            # Float: maximum points possible
    }
  ]
}
```

### Our Adaptation

We'll adapt this format for exercise-level scoring:

```python
{
  "version": 3,
  "status": "pass",  # Overall status: "fail" if any exercise has failures
  "tests": [
    {
      "name": "ex001_sanity",
      "status": "pass",
      "score": 5.0,        # Calculated: (4/4 tests) × 5 weight = 5.0
      "max_score": 5.0,    # From exercise_weights.json
      "output": "4/4 tests passed (100.0%)"
    },
    {
      "name": "ex002_sequence_modify_basics",
      "status": "fail",    # At least one test failed
      "score": 12.0,       # Calculated: (8/10 tests) × 15 weight = 12.0
      "max_score": 15.0,
      "output": "8/10 tests passed (80.0%)\nFailed:\n  - test_exercise4_various_fruits[kiwi]\n  - test_exercise8_edge_case_empty"
    }
  ]
}
```

### Scoring Calculation

From autograding-python-grader's `runner/__init__.py`:

```python
# Their approach: divide max_score evenly among all tests
for test in self.tests.values():
    if test.is_passing():
        test.score = self.results.max_score / len(self.tests)
    else:
        test.score = 0
```

**Our approach:** Weighted per exercise with partial credit:

```python
# For each exercise:
exercise_score = (tests_passed / tests_total) × exercise_weight

# Example:
#   ex002: 8 passed, 10 total, weight = 15
#   exercise_score = (8/10) × 15 = 12.0 points
```

### GitHub Classroom Consumption

The autograding-python-grader outputs to GitHub via:

```bash
# From bin/run.sh
echo "result=$(jq -c . autograding_output/results.json | jq -sRr @base64)" >> "$GITHUB_OUTPUT"
```

We'll follow the same pattern:
1. Write `test-results.json` 
2. Base64 encode it
3. Output to `$GITHUB_OUTPUT`
4. GitHub Classroom autograding action reads it

---

## Files to Create

### 1. `.github/exercise_weights.json`

**Purpose:** Define point allocation for each exercise  
**Location:** `.github/exercise_weights.json`  
**Size:** ~15 lines  
**Format:** JSON dictionary mapping exercise names to point values

**Content:**
```json
{
  "ex001_sanity": 5,
  "ex002_sequence_modify_basics": 15,
  "ex003_sequence_modify_variables": 20,
  "ex004_sequence_debug_syntax": 30,
  "ex005_sequence_debug_logic": 30
}
```

**Schema:**
- **Keys:** Exercise identifiers (must match test file naming: `test_{key}.py`)
- **Values:** Point weights (integer or float, typically sum to 100)
- **Validation:** Total can be any value; percentage calculated automatically

**Usage:**
```python
# Loaded by scoring_plugin.py
weights = json.loads(Path(".github/exercise_weights.json").read_text())
# {"ex001_sanity": 5, "ex002_sequence_modify_basics": 15, ...}
```

---

### 2. `tests/scoring_plugin.py`

**Purpose:** Pytest plugin for weighted exercise scoring  
**Location:** `tests/scoring_plugin.py`  
**Size:** ~250 lines  
**Dependencies:** Python stdlib only (json, pathlib, datetime, typing)

#### Module Structure

```python
"""
Pytest plugin for weighted exercise scoring with GitHub Classroom integration.

This plugin:
1. Loads exercise weights from .github/exercise_weights.json
2. Tags each test with its exercise during collection
3. Records test results grouped by exercise
4. Calculates weighted scores (partial credit for incomplete exercises)
5. Outputs results in GitHub Classroom autograding format
6. Prints detailed breakdown to console

Usage:
    Automatically loaded via pytest.ini configuration.
    No changes to test files required.
    
Configuration:
    Edit .github/exercise_weights.json to adjust point allocations.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest


class ExerciseScoringPlugin:
    """Pytest plugin for weighted exercise scoring."""
    
    def __init__(self) -> None:
        """Initialize plugin and load exercise weights."""
        # Implementation details below
    
    def pytest_collection_modifyitems(self, items: List[pytest.Item]) -> None:
        """Tag each test with its exercise identifier."""
        # Implementation details below
    
    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        """Record test results by exercise."""
        # Implementation details below
    
    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        """Calculate weighted scores and generate reports."""
        # Implementation details below


def pytest_configure(config: pytest.Config) -> None:
    """Register the scoring plugin with pytest."""
    # Implementation details below
```

#### Class: ExerciseScoringPlugin

##### `__init__(self) -> None`

**Purpose:** Initialize plugin and load exercise weights

**Behavior:**
1. Locate weights file at `.github/exercise_weights.json`
2. Load and parse JSON
3. Initialize result tracking dictionary
4. Validate weights format

**Implementation:**
```python
def __init__(self) -> None:
    """Initialize plugin and load exercise weights.
    
    Raises:
        FileNotFoundError: If exercise_weights.json not found
        json.JSONDecodeError: If weights file is invalid JSON
        ValueError: If weights contain invalid values
    """
    # Find weights file relative to repository root
    weights_file = Path(__file__).parent.parent / ".github" / "exercise_weights.json"
    
    if not weights_file.exists():
        raise FileNotFoundError(
            f"Exercise weights file not found: {weights_file}\n"
            "Create .github/exercise_weights.json with exercise point allocations."
        )
    
    try:
        self.weights: Dict[str, float] = json.loads(weights_file.read_text())
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {weights_file}: {e.msg}",
            e.doc,
            e.pos
        )
    
    # Validate weights
    for exercise, weight in self.weights.items():
        if not isinstance(weight, (int, float)) or weight < 0:
            raise ValueError(
                f"Invalid weight for {exercise}: {weight}. "
                "Weights must be non-negative numbers."
            )
    
    # Initialize results tracking: {exercise_name: [test_results]}
    self.results: Dict[str, List[Dict[str, Any]]] = {
        exercise: [] for exercise in self.weights
    }
```

**Error Cases:**
- Missing file → Clear error with creation instructions
- Invalid JSON → Points to syntax error location
- Negative weights → Validation error with exercise name

---

##### `pytest_collection_modifyitems(self, items: List[pytest.Item]) -> None`

**Purpose:** Tag tests with exercise identifiers during collection phase

**Algorithm:**
1. For each collected test item:
   - Extract test file path
   - Parse exercise name from filename
   - Validate against weights
   - Add tag to item.user_properties

**Implementation:**
```python
def pytest_collection_modifyitems(self, items: List[pytest.Item]) -> None:
    """Tag each test with its exercise identifier.
    
    Extracts exercise name from test file path and adds to test metadata.
    Only tests matching 'test_ex###_*.py' pattern are tagged.
    
    Args:
        items: List of collected test items
    """
    for item in items:
        # Extract exercise name from test file path
        # Pattern: test_ex001_sanity.py -> ex001_sanity
        test_file = Path(item.fspath).stem
        exercise = self._extract_exercise_name(test_file)
        
        if exercise and exercise in self.weights:
            # Tag this test as belonging to the exercise
            item.user_properties.append(("exercise", exercise))
        elif exercise:
            # Exercise found but not in weights - warn
            print(f"\nWarning: {test_file}.py has no weight defined in exercise_weights.json")


def _extract_exercise_name(self, test_file_stem: str) -> Optional[str]:
    """Extract exercise identifier from test file name.
    
    Args:
        test_file_stem: Test file name without extension (e.g., 'test_ex001_sanity')
    
    Returns:
        Exercise name (e.g., 'ex001_sanity') or None if not an exercise test
    
    Examples:
        'test_ex001_sanity' -> 'ex001_sanity'
        'test_ex002_modify_basics' -> 'ex002_modify_basics'
        'test_new_exercise' -> None (no ex### prefix)
        'conftest' -> None
    """
    # Must start with 'test_ex' followed by 3 digits
    pattern = r'^test_(ex\d{3}_[a-z_]+)$'
    match = re.match(pattern, test_file_stem)
    return match.group(1) if match else None
```

**Edge Cases:**
- Non-exercise tests (e.g., `test_new_exercise.py`) → Ignored, no warning
- Invalid format (`test_ex2_foo.py`) → Ignored (doesn't match pattern)
- Exercise not in weights → Warning printed, test runs but not scored
- Duplicate test files → Each test tagged independently

---

##### `pytest_runtest_logreport(self, report: pytest.TestReport) -> None`

**Purpose:** Record test execution results grouped by exercise

**Behavior:**
1. Only process "call" phase (ignore setup/teardown)
2. Extract exercise tag from test metadata
3. Record detailed test result
4. Append to exercise's result list

**Implementation:**
```python
def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
    """Record individual test results by exercise.
    
    Called three times per test (setup, call, teardown).
    We only care about the 'call' phase which is the actual test execution.
    
    Args:
        report: Test execution report containing outcome and metadata
    """
    # Only process the actual test call, not setup/teardown
    if report.when != "call":
        return
    
    # Find exercise tag in test metadata
    exercise = None
    for key, value in report.user_properties:
        if key == "exercise":
            exercise = value
            break
    
    # If test is tagged with an exercise, record its result
    if exercise and exercise in self.results:
        self.results[exercise].append({
            "nodeid": report.nodeid,           # Full test identifier
            "passed": report.outcome == "passed",
            "outcome": report.outcome,         # "passed", "failed", "skipped"
            "duration": report.duration,       # Execution time in seconds
        })
```

**Data Structure:**
```python
# self.results after collection
{
  "ex001_sanity": [
    {"nodeid": "tests/test_ex001_sanity.py::test_exercise1_hello", "passed": True, ...},
    {"nodeid": "tests/test_ex001_sanity.py::test_exercise2_math", "passed": True, ...},
  ],
  "ex002_sequence_modify_basics": [
    {"nodeid": "tests/test_ex002_...::test_exercise1", "passed": True, ...},
    {"nodeid": "tests/test_ex002_...::test_exercise4[kiwi]", "passed": False, ...},
  ]
}
```

---

##### `pytest_sessionfinish(self, session: pytest.Session) -> None`

**Purpose:** Calculate final scores and generate outputs

**Responsibilities:**
1. Calculate per-exercise scores
2. Calculate total score
3. Print detailed console breakdown
4. Write JSON results file
5. Determine overall status

**Implementation:**
```python
def pytest_sessionfinish(self, session: pytest.Session) -> None:
    """Calculate weighted scores and generate reports.
    
    Called once after all tests complete. Calculates scores,
    prints breakdown, and writes results.json.
    
    Args:
        session: pytest session containing all test results
    """
    # Calculate scores for each exercise
    exercise_results = {}
    total_earned = 0.0
    total_possible = sum(self.weights.values())
    overall_status = "pass"
    
    for exercise, weight in self.weights.items():
        results = self.results[exercise]
        
        if not results:
            # No tests found for this exercise
            exercise_results[exercise] = {
                "passed": 0,
                "total": 0,
                "score": 0.0,
                "max_score": weight,
                "status": "error",
                "output": "No tests found"
            }
            overall_status = "error"
            continue
        
        # Calculate score: (passed / total) × weight
        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        score = (passed_count / total_count) * weight
        total_earned += score
        
        # Determine status
        if passed_count == total_count:
            status = "pass"
        else:
            status = "fail"
            overall_status = "fail"
        
        # Collect failed test names
        failed_tests = [
            r["nodeid"].split("::")[-1]  # Extract just the test name
            for r in results 
            if not r["passed"]
        ]
        
        # Build output message
        output_lines = [f"{passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)"]
        if failed_tests:
            output_lines.append("Failed:")
            for test in failed_tests[:5]:  # Limit to 5 for readability
                output_lines.append(f"  - {test}")
            if len(failed_tests) > 5:
                output_lines.append(f"  ... and {len(failed_tests) - 5} more")
        
        exercise_results[exercise] = {
            "passed": passed_count,
            "total": total_count,
            "score": score,
            "max_score": weight,
            "status": status,
            "output": "\n".join(output_lines)
        }
    
    # Print detailed breakdown to console
    self._print_summary(exercise_results, total_earned, total_possible)
    
    # Write JSON results file (GitHub Classroom format)
    self._write_results_json(exercise_results, overall_status, total_earned, total_possible)


def _print_summary(
    self, 
    exercise_results: Dict[str, Dict[str, Any]],
    total_earned: float,
    total_possible: float
) -> None:
    """Print detailed score breakdown to console."""
    print("\n" + "=" * 70)
    print("EXERCISE SCORING BREAKDOWN")
    print("=" * 70 + "\n")
    
    for exercise in sorted(exercise_results.keys()):
        result = exercise_results[exercise]
        
        # Format: ex001_sanity    4/  4 tests →   5.00/  5.00 pts (100.0%)
        status_symbol = "✓" if result["status"] == "pass" else "✗"
        print(f"{status_symbol} {exercise:40} "
              f"{result['passed']:3d}/{result['total']:3d} tests → "
              f"{result['score']:6.2f}/{result['max_score']:6.2f} pts "
              f"({result['score']/result['max_score']*100:.1f}%)")
        
        # Show failed tests if any
        if result["status"] == "fail":
            output_lines = result["output"].split("\n")[1:]  # Skip first line (summary)
            for line in output_lines:
                print(f"  {line}")
    
    print("\n" + "=" * 70)
    percentage = (total_earned / total_possible * 100) if total_possible > 0 else 0
    print(f"TOTAL SCORE: {total_earned:.2f}/{total_possible:.2f} ({percentage:.1f}%)")
    print("=" * 70 + "\n")


def _write_results_json(
    self,
    exercise_results: Dict[str, Dict[str, Any]],
    overall_status: str,
    total_earned: float,
    total_possible: float
) -> None:
    """Write results in GitHub Classroom autograding format.
    
    Follows the format specified by autograding-python-grader:
    https://github.com/classroom-resources/autograding-python-grader
    """
    # Build test list in autograding format
    tests = []
    for exercise in sorted(exercise_results.keys()):
        result = exercise_results[exercise]
        tests.append({
            "name": exercise,
            "status": result["status"],
            "score": result["score"],
            "max_score": result["max_score"],
            "output": result["output"]
        })
    
    # Construct full results
    results = {
        "version": 3,
        "status": overall_status,
        "tests": tests,
        # Additional metadata for debugging
        "metadata": {
            "total_earned": total_earned,
            "total_possible": total_possible,
            "percentage": (total_earned / total_possible * 100) if total_possible > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }
    }
    
    # Write to file
    output_file = Path("test-results.json")
    output_file.write_text(json.dumps(results, indent=2))
    print(f"Results written to {output_file}")
```

**Output Format:**
```json
{
  "version": 3,
  "status": "fail",
  "tests": [
    {
      "name": "ex001_sanity",
      "status": "pass",
      "score": 5.0,
      "max_score": 5.0,
      "output": "4/4 tests passed (100.0%)"
    },
    {
      "name": "ex002_sequence_modify_basics",
      "status": "fail",
      "score": 12.0,
      "max_score": 15.0,
      "output": "8/10 tests passed (80.0%)\nFailed:\n  - test_exercise4_various_fruits[kiwi]\n  - test_exercise8_edge_case_empty"
    }
  ],
  "metadata": {
    "total_earned": 78.5,
    "total_possible": 100.0,
    "percentage": 78.5,
    "timestamp": "2026-01-22T14:32:15.123456"
  }
}
```

---

##### Module-level Registration Function

```python
def pytest_configure(config: pytest.Config) -> None:
    """Register the scoring plugin with pytest.
    
    Called automatically by pytest when the module is loaded.
    
    Args:
        config: pytest configuration object
    """
    # Only register on the main process (not on xdist workers)
    if not hasattr(config, "workerinput"):
        config.pluginmanager.register(
            ExerciseScoringPlugin(),
            name="exercise_scoring"
        )
```

---

### 3. `.github/workflows/autograding.yml`

**Purpose:** GitHub Actions workflow for student autograding  
**Location:** `.github/workflows/autograding.yml`  
**Size:** ~60 lines

**Content:**
```yaml
name: Autograding

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

permissions:
  contents: read
  checks: write

jobs:
  grade:
    name: Grade Student Submission
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout student code
      uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Cache uv
      uses: actions/cache@v4
      with:
        path: ~/.cache/uv
        key: ${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}
        restore-keys: |
          ${{ runner.os }}-uv-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip uv
        uv sync

    - name: Run weighted tests
      id: tests
      run: |
        # Run tests with plugin (continue on failure to allow partial credit)
        uv run pytest --tb=short -v || true
        
    - name: Extract and report score
      id: score
      run: |
        if [ -f test-results.json ]; then
          # Extract scores from JSON
          PERCENTAGE=$(jq -r '.metadata.percentage' test-results.json)
          EARNED=$(jq -r '.metadata.total_earned' test-results.json)
          POSSIBLE=$(jq -r '.metadata.total_possible' test-results.json)
          STATUS=$(jq -r '.status' test-results.json)
          
          # Output for GitHub Actions
          echo "percentage=$PERCENTAGE" >> $GITHUB_OUTPUT
          echo "earned=$EARNED" >> $GITHUB_OUTPUT
          echo "possible=$POSSIBLE" >> $GITHUB_OUTPUT
          echo "status=$STATUS" >> $GITHUB_OUTPUT
          
          # Create workflow summary
          echo "### 📊 Test Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Score:** ${EARNED}/${POSSIBLE} points (${PERCENTAGE}%)" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "#### Breakdown by Exercise" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          # Add table of results
          echo "| Exercise | Tests Passed | Score | Status |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|--------------|-------|--------|" >> $GITHUB_STEP_SUMMARY
          
          jq -r '.tests[] | "| \(.name) | \(.output | split("\n")[0]) | \(.score)/\(.max_score) | \(.status) |"' \
            test-results.json >> $GITHUB_STEP_SUMMARY
          
          # Base64 encode for GitHub Classroom compatibility
          RESULT_B64=$(jq -c . test-results.json | base64 -w 0)
          echo "result=$RESULT_B64" >> $GITHUB_OUTPUT
          
        else
          echo "percentage=0" >> $GITHUB_OUTPUT
          echo "earned=0" >> $GITHUB_OUTPUT
          echo "possible=100" >> $GITHUB_OUTPUT
          echo "status=error" >> $GITHUB_OUTPUT
          echo "### ❌ Test Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Error:** No test results found" >> $GITHUB_STEP_SUMMARY
        fi
        
    - name: Upload test results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-results
        path: test-results.json
        retention-days: 30

    - name: Comment on PR (if applicable)
      if: github.event_name == 'pull_request' && always()
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          if (fs.existsSync('test-results.json')) {
            const results = JSON.parse(fs.readFileSync('test-results.json'));
            const metadata = results.metadata;
            
            let body = `## 📊 Test Results\n\n`;
            body += `**Score:** ${metadata.total_earned.toFixed(2)}/${metadata.total_possible.toFixed(2)} (${metadata.percentage.toFixed(1)}%)\n\n`;
            body += `### Breakdown\n\n`;
            
            for (const test of results.tests) {
              const emoji = test.status === 'pass' ? '✅' : '❌';
              body += `${emoji} **${test.name}**: ${test.score.toFixed(2)}/${test.max_score.toFixed(2)}\n`;
            }
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
          }
```

**Key Features:**
- Runs on push/PR to main branch
- Uses `|| true` to continue on test failures (enables partial credit)
- Outputs score to `$GITHUB_OUTPUT` for GitHub Classroom
- Creates detailed workflow summary
- Base64 encodes results for compatibility
- Posts comment on PRs with breakdown
- Uploads JSON artifact for debugging

---

## Files to Modify

### 1. `pytest.ini`

**Location:** `/workspaces/PythonExerciseGeneratorAndDistributor/pytest.ini`

**Current Content:**
```ini
[pytest]
# Keep this file so pytest works even if tools ignore pyproject settings.
# Config is duplicated intentionally for robustness in classroom environments.
addopts = -q
testpaths = tests
pythonpath = .
```

**Required Change:**
Add plugin registration line after `pythonpath = .`

**New Content:**
```ini
[pytest]
# Keep this file so pytest works even if tools ignore pyproject settings.
# Config is duplicated intentionally for robustness in classroom environments.
addopts = -q
testpaths = tests
pythonpath = .
plugins = tests.scoring_plugin
```

**Impact:**
- Pytest automatically loads `scoring_plugin.py` on startup
- No command-line arguments needed
- Works in all environments (local, CI, student repos)

---

### 2. `pyproject.toml`

**Location:** `/workspaces/PythonExerciseGeneratorAndDistributor/pyproject.toml`

**Current Section:**
```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-q"
testpaths = ["tests"]
pythonpath = ["."]
```

**Required Change:**
Add `plugins` line after `pythonpath`

**New Content:**
```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-q"
testpaths = ["tests"]
pythonpath = ["."]
plugins = ["tests.scoring_plugin"]
```

**Impact:**
- Redundant configuration for robustness
- IDE integration support
- Ensures plugin loads even if `pytest.ini` ignored

---

### 3. `template_repo_files/.github/workflows/tests.yml`

**Purpose:** Update template workflow for student repositories

**Location:** `/workspaces/PythonExerciseGeneratorAndDistributor/template_repo_files/.github/workflows/tests.yml`

**Current Content:**
```yaml
    - name: Run tests
      run: |
        pytest -q
```

**Required Changes:**
Replace test execution step with score reporting

**New Content:**
```yaml
    - name: Run weighted tests
      id: tests
      run: |
        # Run tests (continue on failure for partial credit)
        pytest --tb=short -v || true
        
    - name: Display score
      if: always()
      run: |
        if [ -f test-results.json ]; then
          echo "### 📊 Test Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          EARNED=$(jq -r '.metadata.total_earned' test-results.json)
          POSSIBLE=$(jq -r '.metadata.total_possible' test-results.json)
          PERCENTAGE=$(jq -r '.metadata.percentage' test-results.json)
          
          echo "**Score:** ${EARNED}/${POSSIBLE} points (${PERCENTAGE}%)" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "#### Exercise Breakdown" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          jq -r '.tests[] | "- **\(.name):** \(.score)/\(.max_score) pts (\(.status))"' \
            test-results.json >> $GITHUB_STEP_SUMMARY
        fi
```

**Impact:**
- Students see detailed scores in workflow summaries
- Tests don't cause workflow failures (allows partial credit)
- Clear breakdown by exercise

---

### 4. `.github/workflows/tests.yml` (Development Workflow)

**Purpose:** Maintain development testing with solution notebooks

**Location:** `/workspaces/PythonExerciseGeneratorAndDistributor/.github/workflows/tests.yml`

**Current Content:**
```yaml
    - name: Run tests
      env:
        PYTUTOR_NOTEBOOKS_DIR: notebooks/solutions
      run: |
        uv run pytest -q
```

**Optional Enhancement:**
Add score display (doesn't affect functionality, just improves visibility)

**New Content:**
```yaml
    - name: Run tests
      env:
        PYTUTOR_NOTEBOOKS_DIR: notebooks/solutions
      run: |
        uv run pytest -q
        
    - name: Verify solution scoring
      if: always()
      run: |
        if [ -f test-results.json ]; then
          echo "### Development Test Score" >> $GITHUB_STEP_SUMMARY
          EARNED=$(jq -r '.metadata.total_earned' test-results.json)
          POSSIBLE=$(jq -r '.metadata.total_possible' test-results.json)
          
          # Solutions should score 100%
          if (( $(echo "$EARNED == $POSSIBLE" | bc -l) )); then
            echo "✅ Solutions pass all tests: ${EARNED}/${POSSIBLE}" >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ Solutions score: ${EARNED}/${POSSIBLE}" >> $GITHUB_STEP_SUMMARY
            echo "This may indicate a problem with solution notebooks or tests." >> $GITHUB_STEP_SUMMARY
          fi
        fi
```

**Impact:**
- Developers immediately see if solution notebooks don't achieve 100%
- Early detection of test/solution mismatches
- No breaking changes to existing workflow

---

## Detailed Component Specifications

### Score Calculation Formulas

**Per-Exercise Score:**
```
exercise_score = (tests_passed / tests_total) × exercise_weight

Where:
  tests_passed = count of tests with outcome="passed"
  tests_total = count of all tests for this exercise
  exercise_weight = value from exercise_weights.json
```

**Examples:**
```python
# Exercise with all tests passing
ex001: 4 passed, 4 total, weight = 5
score = (4/4) × 5 = 5.0 points

# Exercise with partial success
ex002: 8 passed, 10 total, weight = 15
score = (8/10) × 15 = 12.0 points

# Exercise with no tests passing
ex003: 0 passed, 16 total, weight = 20
score = (0/16) × 20 = 0.0 points

# Exercise not attempted (no tests run)
ex004: 0 passed, 0 total, weight = 30
score = 0.0 points (special case)
```

**Total Score:**
```
total_earned = Σ(exercise_score for each exercise)
total_possible = Σ(exercise_weight for each exercise)
percentage = (total_earned / total_possible) × 100
```

**Overall Status:**
```python
if any exercise has status == "error":
    overall_status = "error"
elif any exercise has status == "fail":
    overall_status = "fail"
else:
    overall_status = "pass"
```

### Test Identification Pattern

**Regex Pattern:**
```python
pattern = r'^test_(ex\d{3}_[a-z_]+)$'
```

**Matches:**
- `test_ex001_sanity.py` → `ex001_sanity`
- `test_ex002_sequence_modify_basics.py` → `ex002_sequence_modify_basics`
- `test_ex010_advanced_loops.py` → `ex010_advanced_loops`

**Non-Matches (ignored):**
- `test_new_exercise.py` (no ex### prefix)
- `test_ex2_foo.py` (only 1 digit, needs 3)
- `test_debug_explanations.py` (no ex### prefix)
- `conftest.py` (no test_ prefix)

### Error Handling

#### Missing Weights File

**Error:**
```
FileNotFoundError: Exercise weights file not found: .github/exercise_weights.json
Create .github/exercise_weights.json with exercise point allocations.
```

**Cause:** Plugin loaded but weights file doesn't exist

**Impact:** pytest fails to start

**Solution:**
```bash
mkdir -p .github
cat > .github/exercise_weights.json << 'EOF'
{
  "ex001_sanity": 5
}
EOF
```

#### Invalid JSON

**Error:**
```
json.JSONDecodeError: Expecting property name enclosed in double quotes: line 2 column 3 (char 4)
```

**Cause:** Syntax error in JSON file

**Impact:** pytest fails to start

**Solution:** Validate JSON:
```bash
jq . .github/exercise_weights.json
```

#### Test Without Weight

**Warning:**
```
Warning: test_ex006_new_topic.py has no weight defined in exercise_weights.json
```

**Cause:** Test file exists but exercise not in weights

**Impact:** Test runs but doesn't contribute to score

**Solution:** Add to weights:
```json
{
  "ex001_sanity": 5,
  "ex006_new_topic": 10
}
```

#### Division by Zero Protection

**Scenario:** Exercise has 0 tests (shouldn't happen but handled)

**Code:**
```python
if total_count == 0:
    score = 0.0
    percentage = 0.0
else:
    score = (passed_count / total_count) * weight
    percentage = (passed_count / total_count) * 100
```

---

## Integration Points

### 1. Pytest Integration

**Hook Execution Order:**
```
1. pytest startup
2. Load plugins (pytest.ini → tests.scoring_plugin)
3. pytest_configure(config) - register plugin instance
4. Collect all test items from test files
5. pytest_collection_modifyitems(items) - tag each test
6. Execute each test:
   - setup
   - call (actual test)
   - teardown
7. For each phase: pytest_runtest_logreport(report)
   - We only process "call" phase
8. pytest_sessionfinish(session) - calculate scores
9. pytest exits
```

**Data Flow:**
```
Test Collection
    ↓
pytest_collection_modifyitems()
    → For each test item:
        → Extract exercise name from file path
        → Add ("exercise", "ex001_sanity") to item.user_properties
    ↓
Test Execution (pytest normal behavior)
    ↓
pytest_runtest_logreport(report)
    → For each test completion:
        → Extract exercise from report.user_properties
        → Record {"passed": True/False, ...} in self.results[exercise]
    ↓
pytest_sessionfinish(session)
    → Calculate scores for each exercise
    → Write test-results.json
    → Print summary
```

### 2. GitHub Actions Integration

**Workflow Execution:**
```
1. Trigger: push/PR to main
2. Checkout student code
3. Set up Python + uv
4. Install dependencies (uv sync)
5. Run: uv run pytest
   ↓
   Plugin executes automatically
   ↓
   test-results.json created
6. Read JSON with jq
7. Extract: percentage, earned, possible
8. Output to $GITHUB_OUTPUT
9. Create workflow summary
10. Upload JSON artifact
```

**Environment Variables:**
- `PYTUTOR_NOTEBOOKS_DIR` - Optional redirect to solutions
- `GITHUB_OUTPUT` - Set by Actions (file path)
- `GITHUB_STEP_SUMMARY` - Set by Actions (file path)

### 3. GitHub Classroom Autograding

**Two Integration Options:**

#### Option A: Direct Integration (Recommended)

Use output variables directly:

```yaml
- name: Autograding
  uses: education/autograding@v1
  with:
    test-name: Python Exercises
    points: ${{ steps.score.outputs.earned }}
    max-points: ${{ steps.score.outputs.possible }}
```

#### Option B: Base64 JSON

Follow autograding-python-grader pattern:

```yaml
- name: Output for Classroom
  run: |
    RESULT_B64=$(jq -c . test-results.json | base64 -w 0)
    echo "result=$RESULT_B64" >> $GITHUB_OUTPUT
```

Then GitHub Classroom can decode and parse the full JSON.

---

## Testing Strategy

### Unit Tests for Plugin

**File:** `tests/test_scoring_plugin.py` (NEW)

**Purpose:** Verify plugin logic independently

**Test Cases:**

```python
"""Unit tests for scoring_plugin.py"""

import json
import tempfile
from pathlib import Path
import pytest
from tests.scoring_plugin import ExerciseScoringPlugin, _extract_exercise_name


def test_extract_exercise_name_valid():
    """Test exercise name extraction from valid test files."""
    plugin = ExerciseScoringPlugin()
    
    assert plugin._extract_exercise_name("test_ex001_sanity") == "ex001_sanity"
    assert plugin._extract_exercise_name("test_ex002_modify_basics") == "ex002_modify_basics"
    assert plugin._extract_exercise_name("test_ex010_advanced") == "ex010_advanced"


def test_extract_exercise_name_invalid():
    """Test exercise name extraction rejects invalid patterns."""
    plugin = ExerciseScoringPlugin()
    
    assert plugin._extract_exercise_name("test_new_exercise") is None
    assert plugin._extract_exercise_name("test_ex2_short") is None
    assert plugin._extract_exercise_name("conftest") is None


def test_score_calculation():
    """Test score calculation for various scenarios."""
    # All tests pass
    assert _calculate_score(passed=10, total=10, weight=15) == 15.0
    
    # Partial pass
    assert _calculate_score(passed=8, total=10, weight=15) == 12.0
    
    # No tests pass
    assert _calculate_score(passed=0, total=10, weight=15) == 0.0
    
    # Edge case: no tests
    assert _calculate_score(passed=0, total=0, weight=15) == 0.0


def test_loads_weights_file(tmp_path):
    """Test that plugin loads weights correctly."""
    # Create temporary weights file
    weights_file = tmp_path / ".github" / "exercise_weights.json"
    weights_file.parent.mkdir(parents=True)
    weights_file.write_text(json.dumps({"ex001_sanity": 5}))
    
    # Mock the file location
    # ... (implementation depends on how we structure the plugin)


def test_missing_weights_file_raises_error():
    """Test that missing weights file raises clear error."""
    with pytest.raises(FileNotFoundError) as exc_info:
        # Try to initialize plugin without weights file
        # ... (implementation)
    
    assert "exercise_weights.json" in str(exc_info.value)
```

### Integration Tests

**File:** `tests/test_integration_scoring.py` (NEW)

**Purpose:** Verify end-to-end scoring workflow

```python
"""Integration tests for scoring system."""

import json
import subprocess
from pathlib import Path
import pytest


def test_scoring_with_solutions():
    """Test that solution notebooks achieve 100% score."""
    result = subprocess.run(
        ["pytest", "-q"],
        env={"PYTUTOR_NOTEBOOKS_DIR": "notebooks/solutions"},
        capture_output=True,
        text=True
    )
    
    # Check results file created
    assert Path("test-results.json").exists()
    
    # Load and verify scores
    results = json.loads(Path("test-results.json").read_text())
    assert results["status"] == "pass"
    assert results["metadata"]["percentage"] == 100.0


def test_scoring_with_incomplete_notebooks():
    """Test partial credit for incomplete work."""
    # This would require creating test fixtures with partial solutions
    # ... (implementation)


def test_json_format_matches_spec():
    """Verify JSON output matches GitHub Classroom format."""
    subprocess.run(["pytest", "-q"], capture_output=True)
    
    results = json.loads(Path("test-results.json").read_text())
    
    # Verify required fields
    assert "version" in results
    assert results["version"] == 3
    assert "status" in results
    assert results["status"] in ["pass", "fail", "error"]
    assert "tests" in results
    assert isinstance(results["tests"], list)
    
    # Verify test format
    for test in results["tests"]:
        assert "name" in test
        assert "status" in test
        assert "score" in test
        assert "max_score" in test
```

### Manual Testing Checklist

Before deployment:

- [ ] Run `pytest -q` locally
- [ ] Verify console output is readable
- [ ] Check `test-results.json` created
- [ ] Verify JSON structure matches spec
- [ ] Test with `PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions`
- [ ] Verify solution notebooks score 100%
- [ ] Test with student notebooks (partial scores)
- [ ] Test with all tests failing
- [ ] Test with mix of pass/fail
- [ ] Verify GitHub Actions workflow runs
- [ ] Check workflow summary displays correctly
- [ ] Verify artifact upload works
- [ ] Test PR comment creation (if enabled)

---

## Deployment Steps

### Phase 1: Local Development & Testing

**Duration:** 1-2 hours

1. **Create weights file:**
   ```bash
   cd /workspaces/PythonExerciseGeneratorAndDistributor
   mkdir -p .github
   cat > .github/exercise_weights.json << 'EOF'
   {
     "ex001_sanity": 5,
     "ex002_sequence_modify_basics": 15,
     "ex003_sequence_modify_variables": 20,
     "ex004_sequence_debug_syntax": 30,
     "ex005_sequence_debug_logic": 30
   }
   EOF
   ```

2. **Create plugin file:**
   ```bash
   # Copy the full implementation from this plan to:
   # tests/scoring_plugin.py
   ```

3. **Update pytest.ini:**
   ```bash
   # Add: plugins = tests.scoring_plugin
   ```

4. **Update pyproject.toml:**
   ```bash
   # Add: plugins = ["tests.scoring_plugin"]
   ```

5. **Test locally against solutions:**
   ```bash
   # Should score 100%
   PYTUTOR_NOTEBOOKS_DIR=notebooks/solutions pytest -q
   
   # Verify output
   cat test-results.json | jq
   ```

6. **Test against student notebooks:**
   ```bash
   # May have failures
   pytest -q
   
   # Check partial credit calculation
   cat test-results.json | jq '.tests[] | {name, score, max_score}'
   ```

7. **Verify edge cases:**
   ```bash
   # Test with missing weights (should error)
   mv .github/exercise_weights.json .github/exercise_weights.json.bak
   pytest -q 2>&1 | grep "FileNotFoundError"
   mv .github/exercise_weights.json.bak .github/exercise_weights.json
   ```

### Phase 2: CI Integration

**Duration:** 30 minutes

8. **Commit changes:**
   ```bash
   git add .github/exercise_weights.json
   git add tests/scoring_plugin.py
   git add pytest.ini
   git add pyproject.toml
   git commit -m "Add weighted exercise scoring plugin"
   ```

9. **Update development workflow (optional):**
   ```bash
   # Edit .github/workflows/tests.yml
   # Add score verification step
   git add .github/workflows/tests.yml
   git commit -m "Add score verification to development workflow"
   ```

10. **Push and verify:**
    ```bash
    git push
    # Check Actions tab for green checkmark
    # Verify solution notebooks score 100%
    ```

11. **Download and inspect artifact:**
    - Go to Actions tab
    - Click on latest run
    - Download test-results artifact
    - Verify JSON structure

### Phase 3: Template Repository Integration

**Duration:** 1 hour

12. **Create autograding workflow:**
    ```bash
    mkdir -p .github/workflows
    # Copy autograding.yml from this plan
    git add .github/workflows/autograding.yml
    git commit -m "Add GitHub Classroom autograding workflow"
    ```

13. **Update template workflows:**
    ```bash
    # Edit template_repo_files/.github/workflows/tests.yml
    # Add score display steps
    git add template_repo_files/.github/workflows/tests.yml
    git commit -m "Update template workflow for score display"
    ```

14. **Copy files to template:**
    ```bash
    # Ensure template includes:
    cp .github/exercise_weights.json template_repo_files/.github/
    cp tests/scoring_plugin.py template_repo_files/tests/
    # (pytest.ini and pyproject.toml should already be in template)
    
    git add template_repo_files/
    git commit -m "Include scoring plugin in template repo"
    ```

### Phase 4: Student Repository Testing

**Duration:** 1-2 hours

15. **Generate test student repository:**
    ```bash
    # Use template_repo_cli to create a test repo
    # Or manually create one for testing
    ```

16. **Test student workflow:**
    - Clone test repo
    - Make changes to notebooks (intentionally incomplete)
    - Commit and push
    - Verify autograding workflow runs
    - Check:
      - Workflow completes successfully (even with test failures)
      - Score appears in workflow summary
      - test-results.json artifact uploaded
      - Partial credit awarded correctly

17. **Test edge cases:**
    - Push with all tests passing → 100%
    - Push with no changes → 0%
    - Push with syntax errors → error status
    - Push with only one exercise complete → proportional score

18. **Document for students:**
    ```bash
    # Update README with scoring explanation
    # Add section showing exercise weights
    # Explain how to view scores
    ```

### Phase 5: Production Deployment & Monitoring

**Duration:** Ongoing

19. **Deploy to first assignment:**
    - Create GitHub Classroom assignment
    - Use template repository
    - Assign to small test group first

20. **Monitor initial submissions:**
    - Check for plugin errors in workflows
    - Verify scores are reasonable
    - Look for edge cases not covered

21. **Collect feedback:**
    - Ask students about clarity of feedback
    - Check if weights align with difficulty
    - Identify any confusion

22. **Iterate:**
    - Adjust weights if needed
    - Fix any discovered edge cases
    - Improve error messages
    - Update documentation

---

## Example Output

### Console Output (pytest)

```
collected 73 items

tests/test_ex001_sanity.py ....                                         [  5%]
tests/test_ex002_sequence_modify_basics.py ........FF.                 [ 20%]
tests/test_ex003_sequence_modify_variables.py ..............F.          [ 42%]
tests/test_ex004_sequence_debug_syntax.py ....................FFFF..   [ 78%]
tests/test_ex005_sequence_debug_logic.py ...F....F.F                   [100%]

======================================================================
EXERCISE SCORING BREAKDOWN
======================================================================

✓ ex001_sanity                                4/  4 tests →   5.00/  5.00 pts (100.0%)

✗ ex002_sequence_modify_basics                8/ 10 tests →  12.00/ 15.00 pts (80.0%)
  Failed:
    - test_exercise4_various_fruits[kiwi]
    - test_exercise8_edge_case_empty

✗ ex003_sequence_modify_variables           14/ 16 tests →  17.50/ 20.00 pts (87.5%)
  Failed:
    - test_exercise10_edge_case
    - test_exercise9_capitals[London]

✗ ex004_sequence_debug_syntax               20/ 26 tests →  23.08/ 30.00 pts (76.9%)
  Failed:
    - test_exercise3_indentation
    - test_exercise5_quotes
    - test_exercise7_parentheses
    - test_exercise8_edge_case
    - test_exercise9_explanation_content

✗ ex005_sequence_debug_logic                 7/ 10 tests →  21.00/ 30.00 pts (70.0%)
  Failed:
    - test_exercise4_off_by_one
    - test_exercise7_loop_logic
    - test_exercise9_edge_case

======================================================================
TOTAL SCORE: 78.58/100.00 (78.6%)
======================================================================

Results written to test-results.json

===================== 12 failed, 61 passed in 4.23s ======================
```

### JSON Output (test-results.json)

```json
{
  "version": 3,
  "status": "fail",
  "tests": [
    {
      "name": "ex001_sanity",
      "status": "pass",
      "score": 5.0,
      "max_score": 5.0,
      "output": "4/4 tests passed (100.0%)"
    },
    {
      "name": "ex002_sequence_modify_basics",
      "status": "fail",
      "score": 12.0,
      "max_score": 15.0,
      "output": "8/10 tests passed (80.0%)\nFailed:\n  - test_exercise4_various_fruits[kiwi]\n  - test_exercise8_edge_case_empty"
    },
    {
      "name": "ex003_sequence_modify_variables",
      "status": "fail",
      "score": 17.5,
      "max_score": 20.0,
      "output": "14/16 tests passed (87.5%)\nFailed:\n  - test_exercise10_edge_case\n  - test_exercise9_capitals[London]"
    },
    {
      "name": "ex004_sequence_debug_syntax",
      "status": "fail",
      "score": 23.08,
      "max_score": 30.0,
      "output": "20/26 tests passed (76.9%)\nFailed:\n  - test_exercise3_indentation\n  - test_exercise5_quotes\n  - test_exercise7_parentheses\n  - test_exercise8_edge_case\n  - test_exercise9_explanation_content"
    },
    {
      "name": "ex005_sequence_debug_logic",
      "status": "fail",
      "score": 21.0,
      "max_score": 30.0,
      "output": "7/10 tests passed (70.0%)\nFailed:\n  - test_exercise4_off_by_one\n  - test_exercise7_loop_logic\n  - test_exercise9_edge_case"
    }
  ],
  "metadata": {
    "total_earned": 78.58,
    "total_possible": 100.0,
    "percentage": 78.58,
    "timestamp": "2026-01-22T14:32:15.123456"
  }
}
```

### GitHub Actions Summary

```markdown
### 📊 Test Results

**Score:** 78.58/100.00 points (78.6%)

#### Breakdown by Exercise

| Exercise | Tests Passed | Score | Status |
|----------|--------------|-------|--------|
| ex001_sanity | 4/4 tests passed (100.0%) | 5.0/5.0 | pass |
| ex002_sequence_modify_basics | 8/10 tests passed (80.0%) | 12.0/15.0 | fail |
| ex003_sequence_modify_variables | 14/16 tests passed (87.5%) | 17.5/20.0 | fail |
| ex004_sequence_debug_syntax | 20/26 tests passed (76.9%) | 23.08/30.0 | fail |
| ex005_sequence_debug_logic | 7/10 tests passed (70.0%) | 21.0/30.0 | fail |

---

Great work! You've completed 78.6% of the exercises.

Focus areas for improvement:
- **ex005_sequence_debug_logic** (70.0%) - Review logic errors carefully
- **ex004_sequence_debug_syntax** (76.9%) - Check syntax and indentation
```

---

## Appendices

### Appendix A: File Locations Summary

```
PythonExerciseGeneratorAndDistributor/
├── .github/
│   ├── exercise_weights.json              # NEW - Point allocations
│   └── workflows/
│       ├── autograding.yml                # NEW - Student autograding
│       ├── tests.yml                      # MODIFY - Add score display
│       └── tests-solutions.yml            # No changes needed
├── tests/
│   ├── scoring_plugin.py                  # NEW - Main plugin (~250 lines)
│   ├── test_scoring_plugin.py             # NEW - Plugin unit tests
│   ├── test_integration_scoring.py        # NEW - Integration tests
│   └── notebook_grader.py                 # No changes needed
├── template_repo_files/
│   ├── .github/
│   │   ├── exercise_weights.json          # COPY from parent
│   │   └── workflows/
│   │       └── tests.yml                  # MODIFY - Student template
│   └── tests/
│       └── scoring_plugin.py              # COPY from parent
├── pytest.ini                              # MODIFY - Add 1 line
├── pyproject.toml                          # MODIFY - Add 1 line
└── PLAN.md                                # THIS FILE
```

### Appendix B: Dependencies

**No new Python dependencies required!**

All functionality uses Python standard library:
- `json` - Parse weights, write results
- `pathlib.Path` - File operations
- `typing` - Type hints
- `datetime` - Timestamps
- `re` - Pattern matching

**Existing dependencies (already installed):**
- `pytest>=8.0` - Test framework

**GitHub Actions dependencies:**
- `jq` - Pre-installed in ubuntu-latest runners
- `base64` - Pre-installed in ubuntu-latest runners

### Appendix C: Rollback Plan

If issues arise after deployment:

**Step 1: Immediate Disable**
```bash
# Comment out plugin in pytest.ini
sed -i 's/^plugins = tests.scoring_plugin/# plugins = tests.scoring_plugin/' pytest.ini
git commit -am "Temporarily disable scoring plugin"
git push
```

**Step 2: Notify Students**
- Post announcement in GitHub Classroom/LMS
- Explain scoring temporarily disabled
- Provide timeline for fix

**Step 3: Fix in Development**
```bash
git checkout -b fix-scoring-plugin
# Fix issues
# Test thoroughly
pytest -q
git push origin fix-scoring-plugin
# Create PR, review, test, merge
```

**Step 4: Re-enable**
```bash
sed -i 's/^# plugins = tests.scoring_plugin/plugins = tests.scoring_plugin/' pytest.ini
git commit -am "Re-enable scoring plugin"
git push
```

### Appendix D: References

**GitHub Classroom Autograding:**
- Repository: https://github.com/classroom-resources/autograding-python-grader
- Documentation: https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding
- Results Format: https://github.com/classroom-resources/autograding-python-grader/blob/main/runner/data.py

**Pytest Plugin Development:**
- Writing Plugins: https://docs.pytest.org/en/stable/how-to/writing_plugins.html
- Hook Reference: https://docs.pytest.org/en/stable/reference/reference.html#hooks
- Plugin List: https://docs.pytest.org/en/stable/reference/plugin_list.html

**This Repository:**
- Testing Framework: `docs/testing-framework.md`
- Project Structure: `docs/project-structure.md`
- Development Guide: `docs/development.md`

### Appendix E: Success Criteria

**Must Have (Phase 1):**
- ✅ Plugin loads without errors
- ✅ All existing tests run successfully
- ✅ Scores calculated correctly for each exercise
- ✅ `test-results.json` created with valid structure
- ✅ Console output shows clear breakdown
- ✅ Works with both student and solution notebooks

**Should Have (Phase 2):**
- ✅ GitHub Actions integration functional
- ✅ Workflow summary displays scores
- ✅ JSON artifact uploaded
- ✅ Parametrized tests contribute proportionally
- ✅ Clear error messages for common issues

**Nice to Have (Phase 3):**
- ⭐ PR comments with score breakdown
- ⭐ Historical score tracking
- ⭐ Email notifications for students
- ⭐ Integration with LMS gradebook
- ⭐ Visual progress indicators

### Appendix F: Future Enhancements

**Version 1.1 - Enhanced Reporting**
- HTML report generation with charts
- Score distribution graphs
- Historical trend tracking per student
- Comparison with class average

**Version 1.2 - Advanced Scoring**
- Per-test weighting within exercises
- Bonus points for code quality/efficiency
- Penalty for late submissions
- Extra credit opportunities

**Version 1.3 - Student Features**
- Hints for failed tests
- Expected vs actual output display
- Suggested exercises based on performance
- Progress badges and achievements

**Version 1.4 - Instructor Tools**
- Bulk score export to CSV
- LMS gradebook integration (Canvas, Moodle, etc.)
- Analytics dashboard
- Automated regrade workflows

---

## Summary

This plan provides a complete implementation path for a weighted exercise scoring system that:

1. **Requires minimal changes** - 3 new files, 2 modified files
2. **Maintains backward compatibility** - existing tests unchanged
3. **Provides detailed feedback** - students see exactly where they need improvement
4. **Integrates with GitHub Classroom** - follows autograding-python-grader format
5. **Supports partial credit** - encourages attempting all exercises
6. **Is maintainable** - configuration-driven, well-documented

The plugin architecture leverages pytest's built-in hooks, requiring no changes to test files. Exercise weights are defined in a simple JSON file, making it easy to adjust point allocations without code changes.

Total implementation time: ~6-8 hours from start to production deployment.

---

**End of Implementation Plan**
