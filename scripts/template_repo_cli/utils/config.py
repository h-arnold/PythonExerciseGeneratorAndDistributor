"""Configuration utilities for template_repo_cli."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast


@dataclass(slots=True)
class TemplateRepoConfig:
    """Configuration settings for the CLI.

    This is intentionally minimal and uses a JSON file for storage to
    avoid external dependencies.
    """

    defaults: dict[str, Any] = field(default_factory=dict[str, Any])


def default_config_path() -> Path:
    """Return the default config path in the user's home directory."""
    return Path.home() / ".template_repo_cli.json"


def _config_object_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Object hook that preserves string keys when loading JSON."""

    return dict(pairs)


def load_config(path: Path | None = None) -> TemplateRepoConfig:
    """Load configuration from disk.

    Args:
        path: Optional custom config path.

    Returns:
        TemplateRepoConfig with loaded defaults (empty if missing).
    """
    config_path = path or default_config_path()
    if not config_path.exists():
        return TemplateRepoConfig()

    raw_data = json.loads(
        config_path.read_text(),
        object_pairs_hook=_config_object_hook,
    )
    if not isinstance(raw_data, dict):
        return TemplateRepoConfig()

    data = cast(dict[str, Any], raw_data)

    return TemplateRepoConfig(defaults=data)


def save_config(config: TemplateRepoConfig, path: Path | None = None) -> None:
    """Save configuration to disk.

    Args:
        config: Configuration object to save.
        path: Optional custom config path.
    """
    config_path = path or default_config_path()
    config_path.write_text(json.dumps(config.defaults, indent=2))
