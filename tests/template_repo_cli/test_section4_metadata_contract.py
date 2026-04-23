"""Section 4 red tests for the template repo metadata contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def section4_dry_run(
    repo_root: Path,
    tmp_path: Path,
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    """Run a template-repo dry run for the Section 4 contract checks."""

    output_dir = tmp_path / "template_output"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/template_repo_cli/cli.py",
            "--dry-run",
            "--output-dir",
            str(output_dir),
            "create",
            "--exercise-keys",
            "ex002_sequence_modify_basics",
            "--repo-name",
            "test-repo",
        ],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    return output_dir, result


def test_dry_run_includes_required_metadata_surfaces(
    section4_dry_run: tuple[Path, subprocess.CompletedProcess[str]],
) -> None:
    """Dry-run packaging should export the required metadata-backed surfaces."""

    output_dir, result = section4_dry_run

    assert result.returncode == 0, (
        "Dry-run packaging did not complete successfully:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    exercise_root = output_dir / "exercises" / "sequence" / "ex002_sequence_modify_basics"
    required_paths = {
        "metadata package": output_dir / "exercise_metadata",
        "metadata package __init__": output_dir / "exercise_metadata" / "__init__.py",
        "metadata registry module": output_dir / "exercise_metadata" / "registry.py",
        "metadata resolver module": output_dir / "exercise_metadata" / "resolver.py",
        "metadata loader module": output_dir / "exercise_metadata" / "loader.py",
        "metadata manifest module": output_dir / "exercise_metadata" / "manifest.py",
        "metadata schema module": output_dir / "exercise_metadata" / "schema.py",
        "migration manifest": output_dir / "exercises" / "migration_manifest.json",
        "per-exercise exercise.json": exercise_root / "exercise.json",
        "student notebook": exercise_root / "notebooks" / "student.ipynb",
        "canonical exercise test": (
            exercise_root / "tests" / "test_ex002_sequence_modify_basics.py"
        ),
    }

    for label, path in required_paths.items():
        assert path.exists(), f"missing {label}: {path}"


def test_dry_run_emits_no_snapshot_artifacts(
    section4_dry_run: tuple[Path, subprocess.CompletedProcess[str]],
) -> None:
    """Dry-run packaging should not emit snapshot artifacts."""

    output_dir, result = section4_dry_run

    assert result.returncode == 0, (
        "Dry-run packaging did not complete successfully:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    snapshot_paths = sorted(
        str(path.relative_to(output_dir)) for path in output_dir.rglob("*snapshot*")
    )
    assert not snapshot_paths, (
        f"dry-run package output must not contain snapshot artifacts: {snapshot_paths}"
    )


def test_dry_run_emits_no_flattened_notebook_or_test_mirrors(
    section4_dry_run: tuple[Path, subprocess.CompletedProcess[str]],
) -> None:
    """Dry-run packaging should not emit flattened notebook or test mirrors."""

    output_dir, result = section4_dry_run

    assert result.returncode == 0, (
        "Dry-run packaging did not complete successfully:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    forbidden_paths = {
        "flattened notebooks directory": output_dir / "notebooks",
        "flattened student notebook": output_dir / "notebooks" / "student.ipynb",
        "flattened solution notebook": output_dir / "notebooks" / "solution.ipynb",
        "flattened exercise test": (output_dir / "tests" / "test_ex002_sequence_modify_basics.py"),
    }

    for label, path in forbidden_paths.items():
        assert not path.exists(), f"forbidden {label} was exported: {path}"


def test_devcontainer_files_exclude_hides_metadata_clutter(
    repo_root: Path,
) -> None:
    """The packaged devcontainer should hide metadata surfaces from Explorer."""

    devcontainer_path = repo_root / "template_repo_files" / ".devcontainer" / "devcontainer.json"
    content = devcontainer_path.read_text(encoding="utf-8").replace(" ", "")

    expected_exclusions = [
        '"exercise_metadata":true',
        '"exercise_metadata/**":true',
        '"exercises/migration_manifest.json":true',
        '"exercises/**/exercise.json":true',
    ]

    for expected in expected_exclusions:
        assert expected in content, (
            f"missing devcontainer files.exclude entry for metadata surface: {expected}"
        )
