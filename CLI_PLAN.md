# CLI Utility for Template Repository Management - Research & Plan

## Executive Summary

**Feasibility**: ✅ **Fully Possible**

All requested features are feasible using Python 3.11+ with the `gh` CLI tool. This document outlines the architecture, implementation plan, and comprehensive test strategy for a modular CLI utility that creates GitHub template repositories containing selected notebooks and tests from this repository.

## Research Findings

### 1. GitHub CLI (`gh`) Capabilities

**Available Features**:
- ✅ Repository creation with template support (`gh repo create`)
- ✅ File operations via `gh api` (GraphQL & REST API)
- ✅ Authentication handling (uses existing `gh auth` credentials)
- ✅ JSON output for parsing (`--json` flag)
- ✅ Template repository flag (`--template` option)

**Limitations Identified**:
- ❌ No native `--dry-run` flag in `gh` commands
- ⚠️ Requires GH_TOKEN environment variable in CI/CD
- ⚠️ API rate limits (5000/hour for authenticated users)

**Workaround for Testing**:
We can implement dry-run mode by:
1. Building the command string without executing
2. Using `subprocess.run` with `capture_output=True` and mocking in tests
3. Validating command structure and parameters before execution
4. Using `gh api --silent` for validation checks (doesn't modify state)

### 2. Repository Structure Analysis

**Current Organization**:
```
notebooks/
  exNNN_slug.ipynb          # Student notebooks
  solutions/
    exNNN_slug.ipynb        # Solution mirrors
tests/
  test_exNNN_slug.py        # Corresponding tests
exercises/
  CONSTRUCT/TYPE/exNNN_slug/
    README.md               # Exercise metadata
```

**Constructs Available**:
- `sequence` - Basic sequential execution
- `selection` - Conditional statements
- `iteration` - Loops
- `data_types` - Type system
- `lists` - List operations
- `dictionaries` - Dictionary operations
- `functions` - Function definitions
- `file_handling` - File I/O
- `exceptions` - Error handling
- `libraries` - External libraries
- `oop` - Object-oriented programming

**Exercise Types**:
- `debug` - Fix broken code
- `modify` - Change working code
- `make` - Create from scratch

**File Relationships**:
- 1:1 mapping: `notebooks/exNNN_slug.ipynb` ↔ `tests/test_exNNN_slug.py`
- Metadata: `exercises/CONSTRUCT/TYPE/exNNN_slug/README.md`
- Both student and solution notebooks must be included

### 3. Template Repository Requirements

**Files to Include**:
1. Selected notebooks (student + solutions)
2. Corresponding test files
3. Exercise metadata (README.md from exercises/)
4. Repository infrastructure:
   - `pyproject.toml` - Python project configuration (micropip-compatible for VS Code web)
   - `pytest.ini` - Test configuration
   - `.gitignore` - Git ignore patterns
   - `README.md` - Customized for the template
   - `.vscode/` - VS Code configuration (settings.json, extensions.json)
   - `tests/notebook_grader.py` - Core grading framework (required for test execution)

**Template Repo Folder** (to be created):
- Location: `/template_repo_files/` at repository root
- Contains: Base files copied to every template repository
- Purpose: Ensures consistent setup across all generated templates

**Notes on GitHub Classroom Integration**:
- GitHub Classroom **does not** automatically create CI workflows for template repositories
- Users must manually configure autograding tests in the Classroom UI or include workflow files
- Since this is a known pain point, we include `.github/workflows/tests.yml` in the template
- This provides immediate CI/CD functionality when students accept assignments

## Proposed Architecture

### Modular Design

```
scripts/
  template_repo_cli/
    __init__.py
    cli.py              # Main entry point (argparse)
    core/
      __init__.py
      selector.py       # Exercise selection logic
      collector.py      # File collection logic
      packager.py       # Template assembly
      github.py         # GitHub operations (gh CLI wrapper)
    utils/
      __init__.py
      validation.py     # Input validation
      filesystem.py     # File operations
      config.py         # Configuration management
tests/
  template_repo_cli/
    __init__.py
    test_selector.py
    test_collector.py
    test_packager.py
    test_github.py
    test_integration.py
```

**Note**: Tests are placed in `tests/template_repo_cli/` to maintain consistency with the repository's existing pattern of keeping all tests in the top-level `tests/` directory.

### Module Responsibilities

#### 1. **cli.py** - Command-Line Interface
- Parse arguments using `argparse`
- Provide subcommands: `create`, `validate`, `list`
- Handle global options: `--dry-run`, `--verbose`, `--output-dir`

#### 2. **selector.py** - Exercise Selection
- Parse user selections:
  - By construct(s): `--construct sequence selection`
  - By type(s): `--type modify debug`
  - By specific notebooks: `--notebooks ex001_sanity ex002_*`
  - Combinations with AND/OR logic
- Validate selections exist
- Return list of exercise IDs

#### 3. **collector.py** - File Collection
- Given exercise IDs, collect:
  - Student notebook paths
  - Solution notebook paths
  - Test file paths
  - Exercise metadata paths
- Validate all required files exist
- Handle missing files gracefully

#### 4. **packager.py** - Template Assembly
- Create temporary directory structure
- Copy selected files to appropriate locations
- Copy base files from `template_repo_files/`:
  - pyproject.toml (micropip-compatible)
  - .vscode/ configuration (settings.json, extensions.json)
  - .github/workflows/ for CI
  - pytest.ini, .gitignore
  - tests/notebook_grader.py
- Generate custom README.md with exercise list
- Validate package integrity

#### 5. **github.py** - GitHub Operations
- Wrapper around `gh` CLI commands
- Check `gh` CLI is installed and prompt user to install if missing
- Verify `gh` authentication status before operations
- Create repository: `gh repo create`
- Push initial commit
- Set repository as template (default behavior)
- Handle authentication errors
- Support dry-run mode (command building without execution)

#### 6. **utils/** - Supporting Utilities
- **validation.py**: Input validation, regex patterns
- **filesystem.py**: Safe file operations, path resolution
- **config.py**: Load/save user preferences

### Command-Line Interface Design

```bash
# Create template from construct
python -m scripts.template_repo_cli create \
  --construct sequence \
  --name "Sequence Exercises Template" \
  --repo-name sequence-exercises

# Create template from multiple constructs
python -m scripts.template_repo_cli create \
  --construct sequence selection \
  --name "Week 1 Exercises" \
  --repo-name week1-exercises

# Create template from specific type within construct
python -m scripts.template_repo_cli create \
  --construct sequence \
  --type modify \
  --name "Sequence Modification Exercises" \
  --repo-name sequence-modify

# Create template from specific notebooks
python -m scripts.template_repo_cli create \
  --notebooks ex001_sanity ex002_sequence_modify_basics \
  --name "Getting Started Exercises" \
  --repo-name getting-started

# Create template with pattern matching
python -m scripts.template_repo_cli create \
  --notebooks "ex00*" \
  --name "First Ten Exercises" \
  --repo-name first-ten

# Dry run (validate without creating)
python -m scripts.template_repo_cli create \
  --construct sequence \
  --dry-run

# List available exercises
python -m scripts.template_repo_cli list \
  --construct sequence

# Validate selection
python -m scripts.template_repo_cli validate \
  --construct sequence \
  --type modify
```

### Flags and Options

**Global Options**:
- `--dry-run` - Build and validate without executing gh commands
- `--verbose` - Show detailed progress
- `--output-dir PATH` - Local output directory (default: temp)

**Create Command Options**:
- `--construct CONSTRUCT [CONSTRUCT...]` - One or more constructs
- `--type TYPE [TYPE...]` - One or more exercise types
- `--notebooks PATTERN [PATTERN...]` - Specific notebook patterns
- `--name NAME` - Template repository name/description
- `--repo-name REPO` - GitHub repository name (slug)
- `--private` - Create as private repository (default: public)
- `--org ORG` - Create in organization (default: user account)
- `--template` - Mark as template repository (default: true)

**List Command Options**:
- `--construct CONSTRUCT` - Filter by construct
- `--type TYPE` - Filter by type
- `--format {table,json,list}` - Output format

**Validate Command Options**:
- Same as create, but only validates selection

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. Create directory structure
2. Set up `pyproject.toml` with dependencies:
   - No additional dependencies needed (use stdlib only)
3. Implement `selector.py`:
   - Parse construct/type/notebook selections
   - Pattern matching for notebooks
   - Validation logic
4. Implement `collector.py`:
   - File discovery
   - Path resolution
   - Missing file handling
5. Write unit tests for selector and collector

### Phase 2: Packaging & GitHub Integration (Week 2)
1. Create `template_repo_files/` directory with base files:
   - pyproject.toml (micropip-compatible)
   - .vscode/settings.json
   - .vscode/extensions.json
   - .github/workflows/tests.yml
   - README.md template
   - pytest.ini
   - .gitignore
2. Implement `packager.py`:
   - Directory assembly
   - File copying
   - README generation
3. Implement `github.py`:
   - Check `gh` CLI is installed (fail early with installation instructions)
   - Verify authentication status
   - `gh` CLI wrapper
   - Command building
   - Dry-run support
   - Error handling
4. Write unit tests with mocking

### Phase 3: CLI Interface (Week 3)
1. Implement `cli.py` with argparse
2. Wire up all modules
3. Add progress indicators
4. Implement verbose mode
5. Write integration tests

### Phase 4: Testing & Documentation (Week 4)
1. Comprehensive test coverage
2. Integration tests with mock GitHub
3. User documentation
4. Example workflows
5. CI/CD integration

## Testing Strategy

### Test Categories

#### 1. Unit Tests (Mock External Dependencies)

**test_selector.py**:
- `test_select_by_single_construct()` - Select all exercises in one construct
- `test_select_by_multiple_constructs()` - Select from multiple constructs
- `test_select_by_construct_and_type()` - Intersection of construct and type
- `test_select_by_specific_notebooks()` - Explicit notebook list
- `test_select_by_pattern()` - Glob pattern matching (ex00*)
- `test_select_invalid_construct()` - Error handling for bad construct
- `test_select_invalid_type()` - Error handling for bad type
- `test_select_nonexistent_notebook()` - Error handling for missing notebook
- `test_select_empty_result()` - Handle no matches gracefully
- `test_select_with_multiple_types()` - Multiple types in one construct

**test_collector.py**:
- `test_collect_all_files_for_exercise()` - Get all related files
- `test_collect_missing_notebook()` - Handle missing student notebook
- `test_collect_missing_solution()` - Handle missing solution notebook
- `test_collect_missing_test()` - Handle missing test file
- `test_collect_missing_metadata()` - Handle missing README.md
- `test_collect_multiple_exercises()` - Batch collection
- `test_collect_validates_paths()` - Path existence validation
- `test_collect_resolves_symlinks()` - Handle symbolic links
- `test_collect_excludes_gitignored()` - Skip ignored files

**test_packager.py**:
- `test_create_temp_directory()` - Temporary workspace creation
- `test_copy_notebooks()` - Copy notebooks to temp directory
- `test_copy_tests()` - Copy test files to temp directory
- `test_copy_template_files()` - Copy base template files
- `test_copy_preserves_structure()` - Maintain directory structure
- `test_generate_readme()` - Create custom README with exercise list
- `test_generate_gitignore()` - Create appropriate .gitignore
- `test_package_integrity_check()` - Validate package completeness
- `test_package_cleanup_on_error()` - Clean up temp files on failure
- `test_package_excludes_solutions_option()` - Optional solution exclusion

**test_github.py**:
- `test_build_create_repo_command()` - Build gh repo create command
- `test_build_create_with_org()` - Organization option
- `test_build_create_private()` - Private repository option
- `test_build_create_template()` - Template repository flag
- `test_execute_gh_command_success()` - Mock successful execution
- `test_execute_gh_command_failure()` - Mock failed execution
- `test_execute_gh_command_auth_error()` - Mock authentication failure
- `test_execute_gh_command_rate_limit()` - Mock rate limit error
- `test_dry_run_does_not_execute()` - Dry run builds but doesn't run
- `test_validate_gh_installed()` - Check gh CLI availability
- `test_validate_gh_authenticated()` - Check gh auth status
- `test_parse_gh_json_output()` - Parse JSON response from gh

**test_validation.py**:
- `test_validate_construct_name()` - Valid construct names
- `test_validate_type_name()` - Valid type names
- `test_validate_repo_name()` - Valid GitHub repo name format
- `test_validate_notebook_pattern()` - Valid pattern syntax
- `test_validate_invalid_construct()` - Reject invalid constructs
- `test_validate_invalid_type()` - Reject invalid types
- `test_validate_invalid_repo_name()` - Reject invalid repo names
- `test_sanitize_repo_name()` - Convert to valid slug

**test_filesystem.py**:
- `test_safe_copy_file()` - Copy file safely
- `test_safe_copy_directory()` - Copy directory recursively
- `test_resolve_notebook_path()` - Resolve relative paths
- `test_create_directory_structure()` - Create nested directories
- `test_atomic_write()` - Write files atomically
- `test_safe_copy_handles_permissions()` - Handle permission errors

#### 2. Integration Tests (Mock Only GitHub API)

**test_integration.py**:
- `test_end_to_end_single_construct()` - Full flow for one construct
- `test_end_to_end_multiple_constructs()` - Full flow for multiple
- `test_end_to_end_specific_notebooks()` - Full flow for specific notebooks
- `test_end_to_end_with_pattern()` - Full flow with pattern matching
- `test_end_to_end_dry_run()` - Full flow in dry-run mode
- `test_end_to_end_error_recovery()` - Error handling in full flow
- `test_cli_help_output()` - Help text generation
- `test_cli_list_command()` - List command output
- `test_cli_validate_command()` - Validate command output
- `test_cli_create_command()` - Create command execution

#### 3. Mock Strategy

**For `subprocess.run` (gh CLI calls)**:
```python
from unittest.mock import patch, MagicMock
import subprocess

@patch('subprocess.run')
def test_gh_create_repo(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='{"name": "test-repo", "html_url": "https://github.com/user/test-repo"}',
        stderr=''
    )
    # Test code here
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert 'gh' in args
    assert 'repo' in args
    assert 'create' in args
```

**For file system operations**:
```python
from unittest.mock import patch, mock_open
import tempfile

def test_with_real_temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use real filesystem in temp directory
        # This is preferred for filesystem tests
```

**For reading repository structure**:
```python
# Use real repository structure for tests
# Tests should run against the actual repo structure
# This validates against real data
```

#### 4. Test Data

**Fixtures** (`tests/fixtures/`):
- `sample_notebooks/` - Minimal notebook examples
- `sample_tests/` - Minimal test examples
- `sample_metadata/` - Sample README.md files
- `expected_outputs/` - Expected generated files

**Test Configuration**:
```python
# conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def repo_root():
    return Path(__file__).parent.parent

@pytest.fixture
def sample_exercises(repo_root):
    return {
        'ex001_sanity': {
            'notebook': repo_root / 'notebooks/ex001_sanity.ipynb',
            'solution': repo_root / 'notebooks/solutions/ex001_sanity.ipynb',
            'test': repo_root / 'tests/test_ex001_sanity.py',
            'metadata': repo_root / 'exercises/ex001_sanity/README.md',
        }
    }

@pytest.fixture
def mock_gh_success():
    with patch('subprocess.run') as mock:
        mock.return_value = MagicMock(returncode=0, stdout='{}', stderr='')
        yield mock
```

## Template Repository Files

### Files to Create in `template_repo_files/`

1. **README.md** (template with placeholders)
```markdown
# {TEMPLATE_NAME}

Python exercises for learning {CONSTRUCTS}.

## Exercises Included

{EXERCISE_LIST}

## Getting Started

1. Clone this repository
2. Install dependencies: `pip install -e ".[dev]"`
3. Open Jupyter: `jupyter lab`
4. Complete exercises and run tests: `pytest -q`

## Testing

Run all tests: `pytest -q`
Run specific test: `pytest tests/test_exNNN_slug.py -v`
```

2. **pyproject.toml** (micropip-compatible for VS Code web)
   - Must only include dependencies available via micropip
   - Enables students to use VS Code for the Web
   - Core dependencies: pytest, ipykernel, jupyterlab
3. **pytest.ini** (identical to main repo)
4. **.gitignore** (standard Python gitignore)
5. **.vscode/settings.json** (VS Code configuration)
   - Python interpreter path
   - Pytest configuration
   - Type checking settings
   - Format on save settings
6. **.vscode/extensions.json** (recommended VS Code extensions)
   - Python extension
   - Pylance
   - Ruff (linter)
   - GitHub Copilot (optional)
7. **.github/workflows/tests.yml** (GitHub Actions CI for autograding)
   - Runs pytest on push/PR
   - Required because GitHub Classroom does not auto-create workflows
8. **tests/notebook_grader.py** (core grading framework - required)
9. **INSTRUCTIONS.md** (student-facing setup and usage instructions)

## Extensibility Points

The modular design allows easy extension:

### Future Features
1. **Export to Zip**: `--export zip` instead of GitHub
2. **Custom Templates**: `--template-dir PATH` for custom base files
3. **Multiple .vscode Configurations**: Templates folder with different configs (web-only, local dev, minimal)
4. **Blackboard/Moodle Export**: Different packaging formats
5. **Student Progress Tracking**: Add analytics notebooks
6. **Difficulty Filtering**: `--difficulty beginner` option
7. **Tag-Based Selection**: `--tags loops,strings` option
8. **Batch Creation**: Create multiple templates from config file
9. **Update Existing**: Update existing template repo with new exercises

### Extension Points in Code
```python
# collector.py - add new file types
class Collector:
    def collect_files(self, exercise_id: str) -> dict[str, Path]:
        return {
            'notebook': self._find_notebook(exercise_id),
            'solution': self._find_solution(exercise_id),
            'test': self._find_test(exercise_id),
            'metadata': self._find_metadata(exercise_id),
            # Easy to add: 'video': self._find_video(exercise_id),
        }

# packager.py - add new output formats
class Packager:
    def package(self, files: dict, format: str = 'github') -> Path:
        if format == 'github':
            return self._package_github(files)
        elif format == 'zip':
            return self._package_zip(files)
        # Easy to add: elif format == 'blackboard':

# github.py - add new operations
class GitHubClient:
    def create_template_repo(self, ...): ...
    # Easy to add:
    # def update_template_repo(self, ...): ...
    # def clone_template_repo(self, ...): ...
```

## Risk Mitigation

### Identified Risks

1. **GitHub API Rate Limits**
   - Mitigation: Cache authentication checks, batch operations
   - Detection: Parse rate limit headers from gh output

2. **Missing Files**
   - Mitigation: Validate all files before packaging
   - Fallback: Warn and skip instead of failing completely

3. **gh CLI Version Compatibility**
   - Mitigation: Check gh version at startup
   - Requirement: Document minimum gh version (2.0.0+)

4. **Authentication Failures**
   - Mitigation: Check auth status before operations
   - User guidance: Show `gh auth login` instructions

5. **Notebook Format Changes**
   - Mitigation: Use existing notebook_grader.py patterns
   - No external dependencies on nbformat

6. **micropip Compatibility (VS Code Web)**
   - Risk: Dependencies in pyproject.toml may not work in VS Code for the Web
   - Mitigation: Validate all dependencies are micropip-compatible
   - Solution: Document micropip constraints in template README
   - Future: Add `--validate-micropip` flag to check dependencies

## Dependencies

**Runtime Dependencies**:
- Python 3.11+ (already required by project)
- `gh` CLI tool (must be installed by user)
- No additional Python packages required (stdlib only)

**Development Dependencies**:
- `pytest` (already in dev dependencies)
- `unittest.mock` (stdlib, for mocking)

**User Requirements**:
- GitHub account
- `gh` CLI installed and authenticated (`gh auth login`)
- Repository permissions to create repos in target org/user

**Template Repository Constraints**:
- **pyproject.toml** must only include micropip-compatible packages
- This ensures compatibility with VS Code for the Web
- All dependencies must be installable without system-level compilation
- Common micropip packages: pytest, ipykernel, jupyterlab, numpy, pandas
- Verify compatibility at: https://pyodide.org/en/stable/usage/packages-in-pyodide.html

## Success Criteria

### Must Have (MVP)
- ✅ Select exercises by construct
- ✅ Select exercises by type
- ✅ Select specific notebooks
- ✅ Create GitHub template repository
- ✅ Dry-run mode for validation
- ✅ Comprehensive test suite (>80% coverage)

### Should Have
- ✅ Pattern matching for notebooks
- ✅ Multiple construct/type selection
- ✅ Custom README generation
- ✅ Progress indicators
- ✅ Verbose mode for debugging

### Nice to Have
- Export to zip (alternative to GitHub)
- Configuration file support
- Batch operations
- Template repo updates

## Timeline Estimate

- **Week 1**: Core modules (selector, collector) + tests
- **Week 2**: Packaging and GitHub integration + tests
- **Week 3**: CLI interface + integration tests
- **Week 4**: Documentation, refinement, CI/CD

**Total**: ~4 weeks for full implementation with comprehensive tests

## Conclusion

**The proposed CLI utility is fully feasible** with the following approach:

1. **Modular Python package** using stdlib only (no extra dependencies)
2. **Wrapper around `gh` CLI** for GitHub operations
3. **Dry-run mode** via command building without execution
4. **Comprehensive testing** with unittest.mock for external calls
5. **Extensible architecture** for future enhancements

All requirements from the problem statement can be met:
- ✅ Modular design for extensibility
- ✅ Uses `gh` CLI (no credential management needed)
- ✅ Select by construct/type/specific notebooks
- ✅ Copies notebooks, tests, and template files
- ✅ Full test suite with mocked gh calls
- ✅ Dry-run capability for testing

The main limitation is that `gh` doesn't have native dry-run, but we can implement this at the application level by building and validating commands without executing them. Tests will mock `subprocess.run` to verify command correctness without making actual GitHub API calls.

## Next Steps

1. **Create `template_repo_files/` directory** with base repository files
2. **Set up module structure** in `scripts/template_repo_cli/`
3. **Implement core modules** (selector, collector) with TDD approach
4. **Add CLI interface** using argparse
5. **Write comprehensive tests** as outlined above
6. **Document usage** with examples and tutorials

---

**Document Version**: 1.0  
**Date**: 2026-01-09  
**Status**: Ready for Implementation
