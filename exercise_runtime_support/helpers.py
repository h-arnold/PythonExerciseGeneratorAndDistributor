"""Autograde environment helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from exercise_runtime_support.execution_variant import (
    configure_variant_environment as _configure_variant_environment,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
__all__ = ["build_autograde_env"]


def build_autograde_env(
    overrides: Mapping[str, str | None] | None = None,
    *,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an environment mapping suitable for invoking autograde helpers."""

    env = dict(base_env or os.environ)
    repo = str(_REPO_ROOT)
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{repo}{os.pathsep}{current}" if current else repo
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    _configure_variant_environment(env, "student")

    if overrides:
        for key, value in overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value

    return env
