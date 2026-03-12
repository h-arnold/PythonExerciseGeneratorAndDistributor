"""exercise_metadata - shared metadata and resolution layer.

This package is the single shared home for exercise metadata loading and path
resolution.  It is importable by scripts/, tests/, and packaged template code
via the repo-root pythonpath.

Contract:
- ``exercise_key`` is the ONLY supported resolver input.
- Path-based resolution is explicitly NOT supported; callers that pass paths
  will receive a TypeError immediately.
- ``PYTUTOR_NOTEBOOKS_DIR`` is ignored entirely; this resolver addresses the
  canonical exercises/ tree, not the legacy notebooks/ tree.
- Canonical behaviour is proved by the live pilot exercise
  ``ex004_sequence_debug_syntax`` which has a full exercise.json and
  notebooks/student.ipynb + notebooks/solution.ipynb in place.
- Resolvers fail hard when an exercise is marked as migrated in
  exercises/migration_manifest.json but its canonical files are missing.
- Legacy exercises remain resolvable as "legacy" via the manifest; callers
  that attempt to get a canonical notebook path for a legacy exercise receive
  a clear error immediately.
"""

from exercise_metadata.loader import load_exercise_metadata
from exercise_metadata.manifest import ExerciseLayout, get_exercise_layout, load_migration_manifest
from exercise_metadata.resolver import resolve_exercise_dir, resolve_notebook_path

__all__ = [
    "ExerciseLayout",
    "get_exercise_layout",
    "load_exercise_metadata",
    "load_migration_manifest",
    "resolve_exercise_dir",
    "resolve_notebook_path",
]
