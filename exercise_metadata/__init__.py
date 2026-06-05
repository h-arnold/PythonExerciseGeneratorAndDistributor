"""exercise_metadata - shared metadata and resolution layer.

This package is the single shared home for exercise metadata loading and path
resolution.  It is importable by scripts/, tests/, and packaged template code
via the repo-root pythonpath.

Contract:
- ``exercise_key`` is the ONLY supported resolver input.
- Path-based resolution is explicitly NOT supported; callers that pass paths
  will receive a TypeError immediately.
- Exercises are discovered by scanning for ``exercise.json`` files under the
  canonical ``exercises/<construct>/<exercise_key>/`` tree.
- All exercises are canonical; there are no legacy exercises.
- Resolvers fail hard when an exercise's canonical files are missing.
"""

from exercise_metadata.loader import load_exercise_metadata
from exercise_metadata.registry import (
    ExerciseCatalogueEntry,
    RegistryEntry,
    build_display_label,
    build_exercise_catalogue,
    build_exercise_registry,
    get_all_exercise_keys,
    get_canonical_exercise_keys,
    get_catalogue_exercise_keys,
)
from exercise_metadata.resolver import resolve_exercise_dir, resolve_notebook_path

__all__ = [
    "ExerciseCatalogueEntry",
    "RegistryEntry",
    "build_display_label",
    "build_exercise_catalogue",
    "build_exercise_registry",
    "get_all_exercise_keys",
    "get_canonical_exercise_keys",
    "get_catalogue_exercise_keys",
    "load_exercise_metadata",
    "resolve_exercise_dir",
    "resolve_notebook_path",
]
