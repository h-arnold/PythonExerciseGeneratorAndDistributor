from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import verify_exercise_quality


def _write_notebook(path: Path, *, include_explanation: bool = True) -> None:
    cells: list[dict[str, object]] = []
    if include_explanation:
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {
                    "language": "markdown",
                    "tags": ["explanation1"],
                },
                "source": ["What actually happened?\n"],
            }
        )

    cells.append(
        {
            "cell_type": "code",
            "metadata": {
                "language": "python",
                "tags": ["exercise1"],
            },
            "source": ["print('Hello')\n"],
        }
    )

    notebook = {"cells": cells}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook), encoding="utf-8")


def _write_teacher_files(exercise_dir: Path) -> None:
    (exercise_dir / "README.md").write_text("# README\n", encoding="utf-8")
    (exercise_dir / "OVERVIEW.md").write_text("# OVERVIEW\n", encoding="utf-8")


def _write_canonical_exercise(
    repo_root: Path,
    slug: str,
    *,
    include_metadata: bool = True,
    exercise_type: str = "debug",
) -> Path:
    exercise_dir = repo_root / "exercises" / "sequence" / slug
    exercise_dir.mkdir(parents=True, exist_ok=True)
    _write_teacher_files(exercise_dir)
    if include_metadata:
        (exercise_dir / "exercise.json").write_text(
            json.dumps(
                {
                    "construct": "sequence",
                    "exercise_type": exercise_type,
                }
            ),
            encoding="utf-8",
        )
    return exercise_dir


def _write_legacy_exercise(repo_root: Path, slug: str, *, exercise_type: str = "debug") -> Path:
    exercise_dir = repo_root / "exercises" / "sequence" / exercise_type / slug
    exercise_dir.mkdir(parents=True, exist_ok=True)
    _write_teacher_files(exercise_dir)
    return exercise_dir


def _write_order_of_teaching(repo_root: Path, slug: str) -> None:
    order_path = repo_root / "exercises" / "sequence" / "OrderOfTeaching.md"
    order_path.parent.mkdir(parents=True, exist_ok=True)
    order_path.write_text(
        f"{slug}\nnotebooks/{slug}.ipynb\n",
        encoding="utf-8",
    )


def test_main_prefers_canonical_layout_when_metadata_exists(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    _write_canonical_exercise(tmp_path, slug)
    (tmp_path / "exercises" / slug).mkdir(parents=True)
    (tmp_path / "exercises" / "sequence" / "debug" / slug).mkdir(parents=True)

    _write_order_of_teaching(tmp_path, slug)

    notebook_path = tmp_path / "notebooks" / f"{slug}.ipynb"
    solution_path = tmp_path / "notebooks" / "solutions" / f"{slug}.ipynb"
    _write_notebook(notebook_path)
    _write_notebook(solution_path)

    exit_code = verify_exercise_quality.main(
        [
            str(notebook_path),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Missing teacher file" not in captured.out
    assert "Could not infer construct" not in captured.out
    assert captured.out.strip().endswith("OK: 0 warning(s)")


def test_main_falls_back_to_legacy_when_canonical_metadata_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    _write_canonical_exercise(tmp_path, slug, include_metadata=False)
    _write_legacy_exercise(tmp_path, slug)
    _write_order_of_teaching(tmp_path, slug)

    notebook_path = tmp_path / "notebooks" / f"{slug}.ipynb"
    solution_path = tmp_path / "notebooks" / "solutions" / f"{slug}.ipynb"
    _write_notebook(notebook_path, include_explanation=False)
    _write_notebook(solution_path, include_explanation=False)

    exit_code = verify_exercise_quality.main(
        [
            str(notebook_path),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Debug exercise expected explanationN tag(s) but none were found" in captured.out
    assert "Invalid JSON in canonical exercise metadata" not in captured.out


def test_main_fails_on_malformed_canonical_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    canonical_dir = _write_canonical_exercise(
        tmp_path, slug, include_metadata=False)
    _write_legacy_exercise(tmp_path, slug)
    _write_order_of_teaching(tmp_path, slug)
    (canonical_dir / "exercise.json").write_text("{", encoding="utf-8")

    notebook_path = tmp_path / "notebooks" / f"{slug}.ipynb"
    solution_path = tmp_path / "notebooks" / "solutions" / f"{slug}.ipynb"
    _write_notebook(notebook_path)
    _write_notebook(solution_path)

    exit_code = verify_exercise_quality.main(
        [
            str(notebook_path),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Invalid JSON in canonical exercise metadata" in captured.out
    assert "Could not infer construct; pass --construct" not in captured.out
    assert captured.out.strip().endswith("FAIL: 1 error(s), 0 warning(s)")


@pytest.mark.parametrize(
    ("metadata", "expected_message"),
    [
        ({"construct": "sequence"},
         "Canonical exercise metadata must define a valid exercise_type"),
        (
            {"construct": "sequence", "exercise_type": "invalid_type"},
            "Canonical exercise metadata must define a valid exercise_type",
        ),
    ],
)
def test_main_fails_when_canonical_metadata_has_no_valid_exercise_type(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    metadata: dict[str, str],
    expected_message: str,
) -> None:
    slug = "ex004_sequence_debug_syntax"
    canonical_dir = _write_canonical_exercise(
        tmp_path,
        slug,
        include_metadata=False,
    )
    _write_legacy_exercise(tmp_path, slug)
    _write_order_of_teaching(tmp_path, slug)
    (canonical_dir / "exercise.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    notebook_path = tmp_path / "notebooks" / f"{slug}.ipynb"
    solution_path = tmp_path / "notebooks" / "solutions" / f"{slug}.ipynb"
    _write_notebook(notebook_path)
    _write_notebook(solution_path)

    exit_code = verify_exercise_quality.main(
        [
            str(notebook_path),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected_message in captured.out
    assert "Debug exercise expected explanationN tag(s) but none were found" not in captured.out
    assert captured.out.strip().endswith("FAIL: 1 error(s), 0 warning(s)")
