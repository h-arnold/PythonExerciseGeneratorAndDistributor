"""Helpers for loading exercise-local Python modules from canonical test folders."""

from __future__ import annotations

import sys
from functools import cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from exercise_runtime_support.exercise_catalogue import get_catalogue_entry

_REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_exercise_tests_dir(exercise_key: str) -> Path:
    """Return the canonical tests directory for an exercise key."""

    entry = get_catalogue_entry(exercise_key)
    source_dir = _REPO_ROOT / "exercises" / entry.construct / exercise_key / "tests"
    if source_dir.is_dir():
        return source_dir

    raise FileNotFoundError(
        "Canonical exercise-local tests directory not found for "
        f"{exercise_key!r}: {source_dir}"
    )


@cache
def load_exercise_test_module(exercise_key: str, module_name: str) -> ModuleType:
    """Load a Python module stored under an exercise-local tests directory."""

    module_path = resolve_exercise_tests_dir(exercise_key) / f"{module_name}.py"
    if not module_path.is_file():
        raise FileNotFoundError(
            f"Exercise-local module {module_name!r} not found for {exercise_key!r}: {module_path}"
        )

    qualified_name = f"_exercise_local_{exercise_key}_{module_name}"
    spec = spec_from_file_location(qualified_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {module_path}")

    module = module_from_spec(spec)
    sys.modules[qualified_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(qualified_name, None)
        raise
    return module


__all__ = ["load_exercise_test_module", "resolve_exercise_tests_dir"]
