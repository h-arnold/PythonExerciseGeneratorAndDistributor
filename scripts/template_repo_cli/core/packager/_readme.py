"""README generation helpers for the template packager."""

from __future__ import annotations

import json
from collections import OrderedDict
from collections.abc import Callable
from pathlib import Path


def load_readme_template(template_files_dir: Path) -> str:
    """Return the README template content, including fallback content.

    Args:
        template_files_dir: Directory containing template files.

    Returns:
        The template content string.
    """
    template_path = template_files_dir / "README.md.template"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "# {TEMPLATE_NAME}\n\n{EXERCISE_LIST}\n"


def readme_entry_from_exercise_key(
    repo_root: Path,
    exercise_key: str,
) -> tuple[str, str, str, str]:
    """Resolve the raw construct, display construct, title, and notebook path.

    Reads exercise.json once and extracts both construct and title from the
    same metadata dict, avoiding a redundant filesystem parse.

    Args:
        repo_root: Root directory of the repository.
        exercise_key: The exercise key.

    Returns:
        Tuple of (raw_construct, display_construct, title, link_target).

    Raises:
        ValueError: If the exercise metadata cannot be read or is invalid.
    """
    try:
        exercise_metadata_path = next(
            (repo_root / "exercises").glob(f"*/{exercise_key}/exercise.json")
        )
        metadata: dict[str, object] = json.loads(exercise_metadata_path.read_text(encoding="utf-8"))
        construct = metadata.get("construct")
        if not isinstance(construct, str) or not construct.strip():
            raise ValueError("missing or invalid construct metadata")
        title = metadata.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("missing or invalid title metadata")
    except Exception as cause:
        reason = str(cause)
        raise ValueError(
            f"README generation failed for exercise '{exercise_key}': {reason}"
        ) from cause

    display_construct = construct.replace("_", " ").title()
    link_target = f"exercises/{construct}/{exercise_key}/notebooks/student.ipynb"
    return construct, display_construct, title, link_target


def render_grouped_readme_sections(
    grouped_entries: OrderedDict[str, list[tuple[str, str]]],
    *,
    constructs_with_resources: dict[str, str] | None = None,
) -> str:
    """Render grouped construct sections with numbered markdown links.

    Args:
        grouped_entries: Mapping of display construct to list of (title, link) tuples.
        constructs_with_resources: Mapping of display-construct name to raw-construct
            slug for constructs that have an additional-resources folder.
            When a construct is in this mapping, a link to the resources folder
            is appended after its exercise list using the raw construct slug.

    Returns:
        Rendered Markdown string.
    """
    if constructs_with_resources is None:
        constructs_with_resources = {}

    sections: list[str] = []
    for display_construct, entries in grouped_entries.items():
        sections.append(f"## {display_construct}")
        for index, (title, link_target) in enumerate(entries, start=1):
            sections.append(f"{index}. [{title}]({link_target})")
        raw_construct = constructs_with_resources.get(display_construct)
        if raw_construct is not None:
            sections.append(
                f"📁 **Additional Resources**: [View resources]"
                f"(exercises/{raw_construct}/additional-resources/)"
            )
        sections.append("")

    return "\n".join(sections).rstrip()


def generate_readme(  # noqa: PLR0913
    repo_root: Path,
    template_files_dir: Path,
    workspace: Path,
    template_name: str,
    exercises: list[str],
    construct_has_resources: Callable[[str], bool],
) -> None:
    """Generate README file.

    Args:
        repo_root: Root directory of the repository.
        template_files_dir: Directory containing template files.
        workspace: Workspace directory.
        template_name: Name of the template.
        exercises: List of exercise keys.
        construct_has_resources: Callable that returns True if a construct
            has an additional-resources folder.
    """
    template_content = load_readme_template(template_files_dir)

    grouped_entries: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()
    constructs_with_resources: dict[str, str] = {}
    for exercise_key in sorted(exercises):
        raw_construct, display_construct, title, link_target = readme_entry_from_exercise_key(
            repo_root, exercise_key
        )
        grouped_entries.setdefault(display_construct, []).append((title, link_target))
        if construct_has_resources(raw_construct):
            constructs_with_resources[display_construct] = raw_construct

    exercise_list = render_grouped_readme_sections(
        grouped_entries,
        constructs_with_resources=constructs_with_resources,
    )
    content = template_content.replace("{TEMPLATE_NAME}", template_name)
    content = content.replace("{EXERCISE_LIST}", exercise_list)
    readme_path = workspace / "README.md"
    readme_path.write_text(content, encoding="utf-8")
