from __future__ import annotations

from pathlib import Path

import pytest

from exercise_runtime_support.pytest_collection_guard import (
    find_duplicate_exercise_test_sources,
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Fail fast when both top-level and canonical exercise tests are collected."""

    root_path = Path(config.rootpath)
    collected_paths = [item.path.relative_to(root_path) for item in items]
    duplicates = find_duplicate_exercise_test_sources(collected_paths)
    if not duplicates:
        return

    duplicate_lines = []
    for exercise_key, paths in sorted(duplicates.items()):
        duplicate_lines.append(f"{exercise_key}:")
        duplicate_lines.extend(f"  - {path}" for path in paths)

    duplicate_report = "\n".join(duplicate_lines)
    raise pytest.UsageError(
        "Duplicate exercise tests were collected from both top-level and canonical "
        f"locations:\n{duplicate_report}"
    )
