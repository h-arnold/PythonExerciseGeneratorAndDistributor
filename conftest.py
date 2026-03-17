from __future__ import annotations

from pathlib import Path

import pytest

from exercise_runtime_support.pytest_collection_guard import (
    find_duplicate_exercise_test_sources,
    find_noncanonical_exercise_test_sources,
)


def _format_path_report(paths: list[Path]) -> str:
    """Return a stable bullet list for pytest usage errors."""

    return "\n".join(f"  - {path}" for path in paths)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Fail fast when collected exercise tests do not follow repository discovery rules."""

    root_path = Path(config.rootpath)
    collected_paths = [item.path.relative_to(root_path) for item in items]

    duplicates = find_duplicate_exercise_test_sources(collected_paths)
    if duplicates:
        duplicate_lines: list[str] = []
        for exercise_key, paths in sorted(duplicates.items()):
            duplicate_lines.append(f"{exercise_key}:")
            duplicate_lines.extend(f"  - {path}" for path in paths)

        duplicate_report = "\n".join(duplicate_lines)
        raise pytest.UsageError(
            "Duplicate exercise tests were collected from both top-level and canonical "
            f"locations:\n{duplicate_report}"
        )

    noncanonical_sources = find_noncanonical_exercise_test_sources(collected_paths)
    if noncanonical_sources:
        raise pytest.UsageError(
            "Noncanonical exercise tests were collected outside "
            "exercises/<construct>/<exercise_key>/tests/:\n"
            f"{_format_path_report(noncanonical_sources)}"
        )
