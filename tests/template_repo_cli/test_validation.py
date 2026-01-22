"""Tests for validation utilities."""

from __future__ import annotations

# Import will fail until we create the module - this is expected for TDD
from scripts.template_repo_cli.utils.validation import (
    sanitize_repo_name,
    validate_construct_name,
    validate_notebook_pattern,
    validate_repo_name,
    validate_type_name,
)


class TestValidateConstructName:
    """Tests for construct name validation."""

    def test_validate_valid_construct_sequence(self) -> None:
        """Test validation of valid construct 'sequence'."""
        assert validate_construct_name("sequence") is True

    def test_validate_valid_construct_selection(self) -> None:
        """Test validation of valid construct 'selection'."""
        assert validate_construct_name("selection") is True

    def test_validate_valid_construct_iteration(self) -> None:
        """Test validation of valid construct 'iteration'."""
        assert validate_construct_name("iteration") is True

    def test_validate_valid_construct_functions(self) -> None:
        """Test validation of valid construct 'functions'."""
        assert validate_construct_name("functions") is True

    def test_validate_invalid_construct(self) -> None:
        """Test validation rejects invalid construct."""
        assert validate_construct_name("invalid_construct") is False

    def test_validate_empty_construct(self) -> None:
        """Test validation rejects empty construct."""
        assert validate_construct_name("") is False

    def test_validate_construct_case_sensitive(self) -> None:
        """Test validation is case-sensitive."""
        assert validate_construct_name("Sequence") is False


class TestValidateTypeName:
    """Tests for exercise type validation."""

    def test_validate_valid_type_debug(self) -> None:
        """Test validation of valid type 'debug'."""
        assert validate_type_name("debug") is True

    def test_validate_valid_type_modify(self) -> None:
        """Test validation of valid type 'modify'."""
        assert validate_type_name("modify") is True

    def test_validate_valid_type_make(self) -> None:
        """Test validation of valid type 'make'."""
        assert validate_type_name("make") is True

    def test_validate_invalid_type(self) -> None:
        """Test validation rejects invalid type."""
        assert validate_type_name("invalid_type") is False

    def test_validate_empty_type(self) -> None:
        """Test validation rejects empty type."""
        assert validate_type_name("") is False

    def test_validate_type_case_sensitive(self) -> None:
        """Test validation is case-sensitive."""
        assert validate_type_name("Debug") is False


class TestValidateRepoName:
    """Tests for repository name validation."""

    def test_validate_valid_repo_name_lowercase(self) -> None:
        """Test validation of valid repo name with lowercase letters."""
        assert validate_repo_name("my-repo") is True

    def test_validate_valid_repo_name_with_numbers(self) -> None:
        """Test validation of valid repo name with numbers."""
        assert validate_repo_name("my-repo-123") is True

    def test_validate_valid_repo_name_with_underscores(self) -> None:
        """Test validation of valid repo name with underscores."""
        assert validate_repo_name("my_repo") is True

    def test_validate_valid_repo_name_mixed(self) -> None:
        """Test validation of valid repo name with mixed characters."""
        assert validate_repo_name("my-repo_2024") is True

    def test_validate_invalid_repo_name_spaces(self) -> None:
        """Test validation rejects repo name with spaces."""
        assert validate_repo_name("my repo") is False

    def test_validate_invalid_repo_name_special_chars(self) -> None:
        """Test validation rejects repo name with special characters."""
        assert validate_repo_name("my@repo") is False

    def test_validate_invalid_repo_name_uppercase(self) -> None:
        """Test validation rejects repo name with uppercase letters."""
        assert validate_repo_name("MyRepo") is False

    def test_validate_empty_repo_name(self) -> None:
        """Test validation rejects empty repo name."""
        assert validate_repo_name("") is False

    def test_validate_repo_name_starts_with_number(self) -> None:
        """Test validation of repo name starting with number."""
        # GitHub allows repo names starting with numbers
        assert validate_repo_name("123-repo") is True

    def test_validate_repo_name_owner_prefix_rejected_by_default(self) -> None:
        """Owner-prefixed names should be rejected unless explicitly allowed."""
        assert validate_repo_name("owner/my-repo") is False

    def test_validate_repo_name_owner_prefix_allowed(self) -> None:
        """Owner-prefixed names are permitted when opted in."""
        assert validate_repo_name("owner/my-repo", allow_owner_prefix=True) is True

    def test_validate_repo_name_owner_prefix_invalid_parts(self) -> None:
        """Owner-prefixed names must follow the same lowercase rules."""
        assert validate_repo_name("Owner/MyRepo", allow_owner_prefix=True) is False


class TestSanitizeRepoName:
    """Tests for repository name sanitization."""

    def test_sanitize_lowercase_conversion(self) -> None:
        """Test sanitization converts to lowercase."""
        assert sanitize_repo_name("MyRepo") == "myrepo"

    def test_sanitize_spaces_to_hyphens(self) -> None:
        """Test sanitization converts spaces to hyphens."""
        assert sanitize_repo_name("my repo") == "my-repo"

    def test_sanitize_special_chars_removed(self) -> None:
        """Test sanitization removes special characters."""
        assert sanitize_repo_name("my@repo!") == "myrepo"

    def test_sanitize_multiple_hyphens(self) -> None:
        """Test sanitization collapses multiple hyphens."""
        assert sanitize_repo_name("my---repo") == "my-repo"

    def test_sanitize_leading_trailing_hyphens(self) -> None:
        """Test sanitization removes leading/trailing hyphens."""
        assert sanitize_repo_name("-my-repo-") == "my-repo"

    def test_sanitize_complex_string(self) -> None:
        """Test sanitization of complex string."""
        assert sanitize_repo_name("My Repo @2024!") == "my-repo-2024"

    def test_sanitize_already_valid(self) -> None:
        """Test sanitization of already valid name."""
        assert sanitize_repo_name("my-repo") == "my-repo"


class TestValidateNotebookPattern:
    """Tests for notebook pattern validation."""

    def test_validate_specific_notebook(self) -> None:
        """Test validation of specific notebook name."""
        assert validate_notebook_pattern("ex001_sanity") is True

    def test_validate_glob_pattern_asterisk(self) -> None:
        """Test validation of glob pattern with asterisk."""
        assert validate_notebook_pattern("ex00*") is True

    def test_validate_glob_pattern_question(self) -> None:
        """Test validation of glob pattern with question mark."""
        assert validate_notebook_pattern("ex00?") is True

    def test_validate_empty_pattern(self) -> None:
        """Test validation rejects empty pattern."""
        assert validate_notebook_pattern("") is False

    def test_validate_pattern_with_slashes(self) -> None:
        """Test validation rejects pattern with slashes."""
        assert validate_notebook_pattern("notebooks/ex001") is False

    def test_validate_pattern_with_special_chars(self) -> None:
        """Test validation accepts pattern with allowed special chars."""
        assert validate_notebook_pattern("ex[0-9]*") is True
