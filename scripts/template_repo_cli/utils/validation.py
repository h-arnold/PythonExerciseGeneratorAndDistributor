"""Input validation utilities."""

from __future__ import annotations

import re

# Valid construct names based on CLI_PLAN.md
VALID_CONSTRUCTS = {
    "sequence",
    "selection",
    "iteration",
    "data_types",
    "lists",
    "dictionaries",
    "functions",
    "file_handling",
    "exceptions",
    "libraries",
    "oop",
}

# Valid exercise types based on CLI_PLAN.md
VALID_TYPES = {"debug", "modify", "make"}


def validate_construct_name(construct: str) -> bool:
    """Validate construct name.

    Args:
        construct: The construct name to validate.

    Returns:
        True if valid, False otherwise.
    """
    return construct in VALID_CONSTRUCTS


def validate_type_name(type_name: str) -> bool:
    """Validate exercise type name.

    Args:
        type_name: The exercise type to validate.

    Returns:
        True if valid, False otherwise.
    """
    return type_name in VALID_TYPES


def validate_repo_name(repo_name: str) -> bool:
    """Validate repository name against this project's convention.

    Our classroom repositories use a simplified, GitHub-compatible
    naming convention for consistency:
    - Only contain lowercase alphanumeric characters, hyphens, or underscores
    - Must not be empty

    Note:
        GitHub itself is more permissive (e.g. allows mixed case), but we
        intentionally enforce this stricter convention here.

    Args:
        repo_name: The repository name to validate.

    Returns:
        True if valid under this convention, False otherwise.
    """
    if not repo_name:
        return False
    # Our convention: lowercase alphanumeric, hyphens, and underscores
    # (stricter than GitHub's actual repository name rules).
    pattern = r"^[a-z0-9_-]+$"
    return bool(re.match(pattern, repo_name))


def sanitize_repo_name(repo_name: str) -> str:
    """Sanitize repository name to this project's canonical format.

    Converts to lowercase, replaces spaces with hyphens,
    removes special characters, and collapses multiple hyphens
    to produce a repository slug that matches ``validate_repo_name``.

    Args:
        repo_name: The repository name (or arbitrary string) to sanitize.

    Returns:
        Sanitized repository name following our lowercase convention.
    """
    # Convert to lowercase
    name = repo_name.lower()

    # Replace spaces with hyphens
    name = name.replace(" ", "-")

    # Remove all characters except alphanumeric, hyphens, and underscores
    name = re.sub(r"[^a-z0-9_-]", "", name)

    # Collapse multiple hyphens into single hyphen
    name = re.sub(r"-+", "-", name)

    # Remove leading and trailing hyphens
    name = name.strip("-")

    return name


def validate_notebook_pattern(pattern: str) -> bool:
    """Validate notebook pattern.

    Pattern must:
    - Not be empty
    - Not contain slashes (path separators)
    - May contain glob characters: *, ?, [, ]

    Args:
        pattern: The notebook pattern to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not pattern:
        return False
    # Reject patterns with path separators
    return not ("/" in pattern or "\\" in pattern)
