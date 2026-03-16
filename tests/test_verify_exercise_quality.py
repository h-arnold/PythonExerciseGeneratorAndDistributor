from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import verify_exercise_quality
from tests.exercise_metadata_helpers import make_exercise_json


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


def _exercise_metadata(
    slug: str,
    *,
    exercise_type: str = "debug",
) -> dict[str, int | str]:
    return {
        "schema_version": 1,
        "exercise_key": slug,
        "exercise_id": 4,
        "slug": slug,
        "title": "Example Exercise",
        "construct": "sequence",
        "exercise_type": exercise_type,
        "parts": 1,
    }


def _write_order_of_teaching(repo_root: Path, slug: str) -> None:
    order_path = repo_root / "exercises" / "sequence" / "OrderOfTeaching.md"
    order_path.parent.mkdir(parents=True, exist_ok=True)
    order_path.write_text(f"{slug}\n", encoding="utf-8")


def _write_canonical_exercise(  # noqa: PLR0913
    repo_root: Path,
    slug: str,
    *,
    include_metadata: bool = True,
    metadata: dict[str, int | str] | None = None,
    include_explanation: bool = True,
    missing_paths: set[str] | None = None,
) -> Path:
    exercise_dir = repo_root / "exercises" / "sequence" / slug
    exercise_dir.mkdir(parents=True, exist_ok=True)
    missing_paths = missing_paths or set()

    if "README.md" not in missing_paths:
        (exercise_dir / "README.md").write_text("# README\n", encoding="utf-8")
    if include_metadata and "exercise.json" not in missing_paths:
        make_exercise_json(exercise_dir, metadata or _exercise_metadata(slug))
    if "notebooks/student.ipynb" not in missing_paths:
        _write_notebook(
            exercise_dir / "notebooks" / "student.ipynb",
            include_explanation=include_explanation,
        )
    if "notebooks/solution.ipynb" not in missing_paths:
        _write_notebook(
            exercise_dir / "notebooks" / "solution.ipynb",
            include_explanation=include_explanation,
        )
    if "tests/test_file" not in missing_paths:
        test_path = exercise_dir / "tests" / f"test_{slug}.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("def test_placeholder() -> None:\n    assert True\n", encoding="utf-8")

    _write_order_of_teaching(repo_root, slug)
    return exercise_dir


def _write_legacy_exercise(repo_root: Path, slug: str) -> None:
    legacy_dir = repo_root / "exercises" / "sequence" / "debug" / slug
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "README.md").write_text("# Legacy README\n", encoding="utf-8")


def test_main_validates_canonical_exercise_layout_successfully(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "ex004_sequence_debug_syntax"
    exercise_dir = _write_canonical_exercise(tmp_path, slug)

    exit_code = verify_exercise_quality.main(
        [
            str(exercise_dir / "notebooks" / "student.ipynb"),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Missing canonical file" not in captured.out
    assert "Could not resolve canonical exercise directory" not in captured.out
    assert captured.out.strip().endswith("OK: 0 warning(s)")


@pytest.mark.parametrize(
    ("missing_path", "expected_message"),
    [
        ("notebooks/solution.ipynb", "Missing canonical file: notebooks/solution.ipynb"),
        (
            "tests/test_file",
            "Missing canonical file: tests/test_ex004_sequence_debug_syntax.py",
        ),
    ],
)
def test_main_fails_when_required_canonical_files_are_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    missing_path: str,
    expected_message: str,
) -> None:
    slug = "ex004_sequence_debug_syntax"
    exercise_dir = _write_canonical_exercise(
        tmp_path,
        slug,
        missing_paths={missing_path},
    )

    exit_code = verify_exercise_quality.main(
        [
            str(exercise_dir / "notebooks" / "student.ipynb"),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected_message in captured.out
    assert captured.out.strip().endswith("FAIL: 1 error(s), 0 warning(s)")


@pytest.mark.parametrize(
    ("metadata", "expected_message"),
    [
        (None, "exercise.json not found"),
        (
            {
                **_exercise_metadata("ex004_sequence_debug_syntax"),
                "exercise_type": "invalid_type",
            },
            "Canonical exercise metadata must define a valid exercise_type",
        ),
    ],
)
def test_main_uses_canonical_metadata_without_legacy_fallback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    metadata: dict[str, int | str] | None,
    expected_message: str,
) -> None:
    slug = "ex004_sequence_debug_syntax"
    exercise_dir = _write_canonical_exercise(
        tmp_path,
        slug,
        include_metadata=metadata is not None,
        metadata=metadata,
        include_explanation=False,
    )
    _write_legacy_exercise(tmp_path, slug)

    exit_code = verify_exercise_quality.main(
        [
            str(exercise_dir / "notebooks" / "student.ipynb"),
            "--repo-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert expected_message in captured.out
    assert "Debug exercise expected explanationN tag(s) but none were found" not in captured.out
    assert captured.out.strip().endswith("FAIL: 1 error(s), 0 warning(s)")
