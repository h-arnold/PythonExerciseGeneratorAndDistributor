# Student Instructions

## Setup

### First Time Setup

1. **Clone the repository** (if you haven't already):

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Install Python** (if you don't have it):
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
   - Verify installation: `python --version` (should show 3.11 or higher)

3. **Install dependencies**:

   - If `uv` is not already installed locally, run:

     ```bash
     python -m pip install --upgrade pip uv
     ```

   - Sync the repository stack with `uv`:

     ```bash
     uv sync
     ```

4. **Start Jupyter Lab**:

   ```bash
   jupyter lab
   ```

## How to Complete Exercises

### Understanding the Notebook Structure

Each exercise notebook contains:

- **Instructions**: What you need to do
- **Code cells**: Where you write your solution
- **Metadata tags**: Special markers (like `exercise1`) that tell the testing system which cells to test

### Writing Solutions

1. Open an exercise notebook (e.g., `notebooks/ex001_sanity.ipynb`)
2. Read the instructions carefully
3. Find the cell tagged for the exercise (look for the tag in the cell metadata)
4. Write your code in that cell
5. Run the cell to check for syntax errors
6. Run the tests to verify your solution

### Cell Metadata Tags

The testing system uses cell metadata tags to identify which cells contain your solutions:

- `exercise1` - Your solution for exercise 1
- `exercise2` - Your solution for exercise 2
- etc.

**Important**: Don't modify these tags or remove them!

## Testing Your Work

### Run All Tests

```bash
pytest -q
```

### Run Tests for One Exercise

```bash
pytest tests/test_ex001_sanity.py -v
```

### Understanding Test Output

**Passing test**:

```
test_example_returns_string PASSED
```

**Failing test**:

```
test_example_returns_string FAILED
AssertionError: Expected 'hello' but got 'hi'
```

The error message tells you what went wrong!

## Common Issues

### "Module not found" error

- Make sure you installed dependencies: `uv sync`
- Try reinstalling the stack by running `uv sync` again

### Tests won't run

- Check you're in the repository root directory
- Verify pytest is installed: `pytest --version`

### Can't start Jupyter

- Make sure you installed the dev dependencies (`uv sync`)
- Try: `jupyter lab`

### My code works in Jupyter but tests fail

- Check you're modifying the correct cell (check the tag!)
- Make sure your cell output matches what the test expects
- Read the test error message carefully

## Tips for Success

1. **Read instructions carefully** - Make sure you understand what's being asked
2. **Start simple** - Get something working first, then improve it
3. **Test frequently** - Don't wait until you've completed everything
4. **Use print statements** - Debug by printing intermediate values
5. **Check the solutions** - If you're stuck, look at `notebooks/solutions/` for hints
6. **Ask for help** - Don't struggle alone - ask your instructor!

## VS Code for the Web

This repository is compatible with VS Code for the Web! You can work on exercises directly in your browser:

1. Go to github.dev and open your repository
2. Install recommended extensions
3. Start coding!

Note: Some features (like running notebooks) may have limitations in the web version.

## Getting Help

- **Test errors**: Read the error message - it often tells you exactly what's wrong
- **Python syntax**: Use the official [Python documentation](https://docs.python.org/)
- **Stuck on logic**: Try explaining your approach out loud (rubber duck debugging!)
- **Still stuck**: Ask your instructor

Good luck! 🐍
