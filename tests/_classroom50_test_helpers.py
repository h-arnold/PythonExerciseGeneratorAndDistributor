"""Shared helpers for the Classroom 50 bundle grading tests.

``tests/test_classroom50_bundle_stage4.py`` and
``tests/test_classroom50_native_autograder.py`` both drive the bundle-local
``autograder.py`` child, both write synthetic canonical ``exercise.json`` files,
and both assert the canonical ``<exercise_key>::<leaf-nodeid>`` result-row naming
rule.  Expressing those three pieces here keeps the contract identical in both
modules so it cannot drift.

The staged fixtures themselves are deliberately *not* shared: the stage-4 module
stages a *source tree* for ``scripts/build_classroom50_bundle.py`` to consume,
while the native module stages a *bundle* directly for a no-argument child.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CHILD_TIMEOUT_SECONDS = 120
AUTOGRADER_FILENAME = "autograder.py"


@dataclass(frozen=True)
class SyntheticExercise:
    """Identity of one synthetic canonical exercise used by a bundle fixture."""

    exercise_key: str
    exercise_id: int
    construct: str
    title: str
    exercise_type: str = "make"


def run_bundle_child(
    bundle_root: Path,
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = DEFAULT_CHILD_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run the bundle-local ``autograder.py`` child with exactly ``args``.

    Args:
        bundle_root: Directory holding the bundle-local ``autograder.py``.
        args: Exact child argument vector. An empty list is the native invocation.
        cwd: Child working directory; ``None`` inherits the current one.
        env: Child environment; ``None`` inherits the current process environment.
        timeout: Seconds before the child is abandoned.

    Returns:
        The completed child process with captured text streams.
    """
    return subprocess.run(
        [sys.executable, str(bundle_root / AUTOGRADER_FILENAME), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def write_synthetic_exercise_json(exercise_dir: Path, exercise: SyntheticExercise) -> Path:
    """Write a canonical synthetic ``exercise.json`` into ``exercise_dir``.

    The metadata mirrors the field set ``exercise_metadata.loader`` requires, so
    the canonical resolver accepts the synthetic exercise in an isolated
    ``tmp_path`` checkout.

    Args:
        exercise_dir: Canonical exercise directory that receives the file.
        exercise: Identity the written metadata must declare.

    Returns:
        Path to the written ``exercise.json``.
    """
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "exercise_key": exercise.exercise_key,
        "exercise_id": exercise.exercise_id,
        "slug": exercise.exercise_key,
        "title": exercise.title,
        "construct": exercise.construct,
        "exercise_type": exercise.exercise_type,
        "parts": 1,
    }
    path = exercise_dir / "exercise.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    return path


def expected_row_name(exercise_key: str, leaf_node_id: str) -> str:
    """Return the canonical ``<exercise_key>::<leaf-nodeid>`` result-row name.

    The leaf portion is the ``test_*.py::test_name`` tail of the pytest node id
    and never contains an absolute path.
    """
    return f"{exercise_key}::{leaf_node_id}"
