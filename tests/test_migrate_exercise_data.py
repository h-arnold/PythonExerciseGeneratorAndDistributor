from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import migrate_exercise_data

_EX002 = "ex002_sequence_modify_basics"
_EX006 = "ex006_sequence_modify_casting"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_notebook(path: Path, marker: str) -> None:
    _write_json(
        path,
        {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {
                        "id": f"cell_{marker}",
                        "language": "python",
                    },
                    "source": [f"print({marker!r})\n"],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        },
    )


def _write_exercise_json(repo_root: Path, exercise_key: str, exercise_type: str) -> None:
    exercise_dir = repo_root / "exercises" / "sequence" / exercise_key
    exercise_id = int(exercise_key[2:5])
    _write_json(
        exercise_dir / "exercise.json",
        {
            "schema_version": 1,
            "exercise_key": exercise_key,
            "exercise_id": exercise_id,
            "slug": exercise_key,
            "title": exercise_key,
            "construct": "sequence",
            "exercise_type": exercise_type,
            "parts": 1,
        },
    )
    _write_text(
        exercise_dir / "tests" / f"test_{exercise_key}.py",
        "def test_placeholder() -> None:\n    assert True\n",
    )


def _snapshot_files(repo_root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(repo_root).as_posix(): path.read_bytes()
        for path in sorted(repo_root.rglob("*"))
        if path.is_file()
    }


def _snapshot_directories(repo_root: Path) -> set[str]:
    return {
        path.relative_to(repo_root).as_posix()
        for path in sorted(repo_root.rglob("*"))
        if path.is_dir()
    }


def _build_repo_fixture(repo_root: Path) -> None:
    _write_json(
        repo_root / "exercises" / "migration_manifest.json",
        {
            "schema_version": 1,
            "_comment": "layout state",
            "exercises": {
                _EX002: {"layout": "legacy"},
                _EX006: {"layout": "legacy"},
            },
        },
    )
    _write_text(
        repo_root / "exercises" / "sequence" / "OrderOfTeaching.md",
        "# Order of teaching\n\n"
        f"1. [Modify Basics](`{_EX002}`)\n\n"
        f"[Supporting docs](./modify/{_EX002}/)\n"
        f"[Notebook](notebooks/{_EX002}.ipynb)\n\n"
        f"1. [Casting](`{_EX006}`)\n\n"
        f"[Supporting docs](./{_EX006}/)\n"
        f"[Notebook](notebooks/{_EX006}.ipynb)\n",
    )

    _write_exercise_json(repo_root, _EX002, "modify")
    _write_text(
        repo_root / "exercises" / "sequence" / "modify" / _EX002 / "README.md",
        "# Sequence Modification Basics\n\n"
        f"- Open the matching notebook in `notebooks/{_EX002}.ipynb`.\n"
        "- Run `pytest -q tests/test_placeholder.py` if you are experimenting.\n"
        f"- Run `pytest -q exercises/sequence/{_EX002}/tests/test_{_EX002}.py` until all tests pass.\n",
    )
    _write_text(
        repo_root / "exercises" / "sequence" / "modify" / _EX002 / "OVERVIEW.md",
        "# Overview\n\n"
        f"- **Notebook**: [notebooks/{_EX002}.ipynb](../../../../notebooks/{_EX002}.ipynb)\n"
        f"- **Solution**: [notebooks/solutions/{_EX002}.ipynb]"
        f"(../../../../notebooks/solutions/{_EX002}.ipynb)\n"
        f"- **Tests**: [exercises/sequence/{_EX002}/tests/test_{_EX002}.py]"
        f"(../../{_EX002}/tests/test_{_EX002}.py)\n"
        f"- **Exercise folder**: [exercises/sequence/modify/{_EX002}/](./)\n",
    )
    _write_text(
        repo_root / "exercises" / "sequence" / "modify" / _EX002 / "__init__.py",
        "",
    )
    _write_notebook(repo_root / "notebooks" / f"{_EX002}.ipynb", "student ex002")
    _write_notebook(
        repo_root / "notebooks" / "solutions" / f"{_EX002}.ipynb",
        "solution ex002",
    )

    _write_exercise_json(repo_root, _EX006, "modify")
    _write_text(
        repo_root / "exercises" / "sequence" / _EX006 / "README.md",
        "# ex006\n\n"
        f"- **Notebook path**: `notebooks/{_EX006}.ipynb`\n"
        f"- **Solution path**: `notebooks/solutions/{_EX006}.ipynb`\n"
        f"- **Tests path**: `exercises/sequence/{_EX006}/tests/test_{_EX006}.py`\n"
        "- Open the matching notebook in `notebooks/`.\n"
        "- Run `pytest -q` until all tests pass.\n",
    )
    _write_text(
        repo_root / "exercises" / "sequence" / _EX006 / "OVERVIEW.md",
        "# Overview\n\n"
        f"Use [notebooks/{_EX006}.ipynb](notebooks/{_EX006}.ipynb) and "
        f"`exercises/sequence/{_EX006}/tests/test_{_EX006}.py`.\n",
    )
    _write_notebook(repo_root / "notebooks" / f"{_EX006}.ipynb", "student ex006")
    _write_notebook(
        repo_root / "notebooks" / "solutions" / f"{_EX006}.ipynb",
        "solution ex006",
    )


def test_dry_run_reports_actions_without_mutating_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _build_repo_fixture(tmp_path)
    before_files = _snapshot_files(tmp_path)
    before_directories = _snapshot_directories(tmp_path)

    exit_code = migrate_exercise_data.main(
        [
            "--construct",
            "sequence",
            "--repo-root",
            str(tmp_path),
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Mode: dry-run" in captured.out
    assert f"move notebooks/{_EX002}.ipynb -> exercises/sequence/{_EX002}/notebooks/student.ipynb" in captured.out
    assert f"rewrite local links in exercises/sequence/{_EX002}/README.md" in captured.out
    assert "update canonical notebook/supporting-doc links in exercises/sequence/OrderOfTeaching.md" in captured.out
    assert "Remaining legacy sources:" in captured.out
    assert f"notebooks/{_EX002}.ipynb" in captured.out
    assert f"exercises/sequence/modify/{_EX002}" in captured.out

    assert _snapshot_files(tmp_path) == before_files
    assert _snapshot_directories(tmp_path) == before_directories
    manifest = json.loads(
        (tmp_path / "exercises" / "migration_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["exercises"][_EX002]["layout"] == "legacy"
    assert manifest["exercises"][_EX006]["layout"] == "legacy"






def test_apply_mode_migrates_notebooks_docs_manifest_and_teaching_order(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _build_repo_fixture(tmp_path)

    exit_code = migrate_exercise_data.main(
        [
            "--construct",
            "sequence",
            "--repo-root",
            str(tmp_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Mode: apply" in captured.out
    assert "Remaining legacy sources:\n- none" in captured.out

    ex002_dir = tmp_path / "exercises" / "sequence" / _EX002
    ex006_dir = tmp_path / "exercises" / "sequence" / _EX006

    assert json.loads((ex002_dir / "notebooks" / "student.ipynb").read_text(encoding="utf-8"))[
        "cells"
    ][0]["source"] == ["print('student ex002')\n"]
    assert json.loads((ex002_dir / "notebooks" / "solution.ipynb").read_text(encoding="utf-8"))[
        "cells"
    ][0]["source"] == ["print('solution ex002')\n"]
    assert json.loads((ex006_dir / "notebooks" / "student.ipynb").read_text(encoding="utf-8"))[
        "cells"
    ][0]["source"] == ["print('student ex006')\n"]
    assert json.loads((ex006_dir / "notebooks" / "solution.ipynb").read_text(encoding="utf-8"))[
        "cells"
    ][0]["source"] == ["print('solution ex006')\n"]

    assert not (tmp_path / "notebooks" / f"{_EX002}.ipynb").exists()
    assert not (tmp_path / "notebooks" / "solutions" / f"{_EX002}.ipynb").exists()
    assert not (tmp_path / "notebooks" / f"{_EX006}.ipynb").exists()
    assert not (tmp_path / "notebooks" / "solutions" / f"{_EX006}.ipynb").exists()
    assert not (tmp_path / "exercises" / "sequence" / "modify" / _EX002).exists()

    ex002_readme = (ex002_dir / "README.md").read_text(encoding="utf-8")
    ex002_overview = (ex002_dir / "OVERVIEW.md").read_text(encoding="utf-8")
    ex006_readme = (ex006_dir / "README.md").read_text(encoding="utf-8")
    ex006_overview = (ex006_dir / "OVERVIEW.md").read_text(encoding="utf-8")

    assert "`notebooks/student.ipynb`" in ex002_readme
    assert f"tests/test_{_EX002}.py" in ex002_readme
    assert "[notebooks/student.ipynb](notebooks/student.ipynb)" in ex002_overview
    assert "[notebooks/solution.ipynb](notebooks/solution.ipynb)" in ex002_overview
    assert f"[tests/test_{_EX002}.py](tests/test_{_EX002}.py)" in ex002_overview
    assert f"exercises/sequence/{_EX002}/" in ex002_overview

    assert "`notebooks/student.ipynb`" in ex006_readme
    assert "`notebooks/solution.ipynb`" in ex006_readme
    assert f"`tests/test_{_EX006}.py`" in ex006_readme
    assert f"Run `pytest -q tests/test_{_EX006}.py` until all tests pass." in ex006_readme
    assert "[notebooks/student.ipynb](notebooks/student.ipynb)" in ex006_overview
    assert f"`tests/test_{_EX006}.py`" in ex006_overview

    order_of_teaching = (
        tmp_path / "exercises" / "sequence" / "OrderOfTeaching.md"
    ).read_text(encoding="utf-8")
    assert f"[Supporting docs](./{_EX002}/)" in order_of_teaching
    assert f"[Notebook](./{_EX002}/notebooks/student.ipynb)" in order_of_teaching
    assert f"[Supporting docs](./{_EX006}/)" in order_of_teaching
    assert f"[Notebook](./{_EX006}/notebooks/student.ipynb)" in order_of_teaching

    manifest = json.loads(
        (tmp_path / "exercises" / "migration_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["exercises"][_EX002]["layout"] == "canonical"
    assert manifest["exercises"][_EX006]["layout"] == "canonical"


def test_apply_mode_fails_on_mismatched_destination_content(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _build_repo_fixture(tmp_path)
    _write_notebook(
        tmp_path / "exercises" / "sequence" / _EX002 / "notebooks" / "student.ipynb",
        "canonical ex002",
    )

    exit_code = migrate_exercise_data.main(
        [
            "--construct",
            "sequence",
            "--repo-root",
            str(tmp_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert f"exercises/sequence/{_EX002}/notebooks/student.ipynb" in captured.out
    assert f"notebooks/{_EX002}.ipynb" in captured.out
    assert "already exists and differs" in captured.out
    assert (tmp_path / "notebooks" / f"{_EX002}.ipynb").exists()
    assert (tmp_path / "exercises" / "sequence" / "modify" / _EX002).exists()

    manifest = json.loads(
        (tmp_path / "exercises" / "migration_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["exercises"][_EX002]["layout"] == "legacy"


def test_apply_mode_fails_when_required_notebook_is_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _build_repo_fixture(tmp_path)
    missing_student_notebook = tmp_path / "notebooks" / f"{_EX002}.ipynb"
    missing_student_notebook.unlink()
    before_files = _snapshot_files(tmp_path)
    before_directories = _snapshot_directories(tmp_path)

    exit_code = migrate_exercise_data.main(
        [
            "--construct",
            "sequence",
            "--repo-root",
            str(tmp_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert f"Missing required student notebook for {_EX002}" in captured.out
    assert f"notebooks/{_EX002}.ipynb" in captured.out
    assert f"exercises/sequence/{_EX002}/notebooks/student.ipynb" in captured.out
    assert _snapshot_files(tmp_path) == before_files
    assert _snapshot_directories(tmp_path) == before_directories

    manifest = json.loads(
        (tmp_path / "exercises" / "migration_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["exercises"][_EX002]["layout"] == "legacy"


def test_apply_mode_retries_successfully_after_manifest_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _build_repo_fixture(tmp_path)
    original_apply_write = migrate_exercise_data._apply_write
    manifest_path = tmp_path / "exercises" / "migration_manifest.json"
    manifest_before = manifest_path.read_text(encoding="utf-8")
    canonical_readme_path = tmp_path / "exercises" / "sequence" / _EX002 / "README.md"
    legacy_shadow_readme_path = (
        tmp_path / "exercises" / "sequence" / "modify" / _EX002 / "README.md"
    )

    def _failing_apply_write(action: migrate_exercise_data.Action) -> None:
        if action.destination == manifest_path:
            raise OSError("simulated manifest write failure")
        original_apply_write(action)

    monkeypatch.setattr(migrate_exercise_data, "_apply_write", _failing_apply_write)

    exit_code = migrate_exercise_data.main(
        [
            "--construct",
            "sequence",
            "--repo-root",
            str(tmp_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "simulated manifest write failure" in captured.out
    assert (tmp_path / "notebooks" / f"{_EX002}.ipynb").exists()
    assert (tmp_path / "notebooks" / "solutions" / f"{_EX002}.ipynb").exists()
    assert (tmp_path / "notebooks" / f"{_EX006}.ipynb").exists()
    assert (tmp_path / "notebooks" / "solutions" / f"{_EX006}.ipynb").exists()
    assert (tmp_path / "exercises" / "sequence" / "modify" / _EX002).exists()
    assert (tmp_path / "exercises" / "sequence" / "modify" / _EX002 / "README.md").exists()
    assert manifest_path.read_text(encoding="utf-8") == manifest_before
    assert canonical_readme_path.exists()
    assert legacy_shadow_readme_path.exists()
    assert canonical_readme_path.read_text(encoding="utf-8") != legacy_shadow_readme_path.read_text(
        encoding="utf-8"
    )

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    assert manifest["exercises"][_EX002]["layout"] == "legacy"
    assert manifest["exercises"][_EX006]["layout"] == "legacy"

    monkeypatch.setattr(migrate_exercise_data, "_apply_write", original_apply_write)

    retry_exit_code = migrate_exercise_data.main(
        [
            "--construct",
            "sequence",
            "--repo-root",
            str(tmp_path),
            "--apply",
        ]
    )
    retry_captured = capsys.readouterr()

    assert retry_exit_code == 0
    assert "Mode: apply" in retry_captured.out
    assert "Remaining legacy sources:\n- none" in retry_captured.out

    ex002_dir = tmp_path / "exercises" / "sequence" / _EX002
    ex006_dir = tmp_path / "exercises" / "sequence" / _EX006

    assert (ex002_dir / "notebooks" / "student.ipynb").exists()
    assert (ex002_dir / "notebooks" / "solution.ipynb").exists()
    assert (ex006_dir / "notebooks" / "student.ipynb").exists()
    assert (ex006_dir / "notebooks" / "solution.ipynb").exists()
    assert not (tmp_path / "notebooks" / f"{_EX002}.ipynb").exists()
    assert not (tmp_path / "notebooks" / "solutions" / f"{_EX002}.ipynb").exists()
    assert not (tmp_path / "notebooks" / f"{_EX006}.ipynb").exists()
    assert not (tmp_path / "notebooks" / "solutions" / f"{_EX006}.ipynb").exists()
    assert not (tmp_path / "exercises" / "sequence" / "modify" / _EX002).exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["exercises"][_EX002]["layout"] == "canonical"
    assert manifest["exercises"][_EX006]["layout"] == "canonical"


def test_apply_mode_removes_duplicate_identical_legacy_notebook_after_success(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _build_repo_fixture(tmp_path)
    canonical_student_notebook = (
        tmp_path / "exercises" / "sequence" / _EX002 / "notebooks" / "student.ipynb"
    )
    _write_notebook(canonical_student_notebook, "student ex002")

    exit_code = migrate_exercise_data.main(
        [
            "--construct",
            "sequence",
            "--repo-root",
            str(tmp_path),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"remove duplicate legacy file notebooks/{_EX002}.ipynb" in captured.out
    assert canonical_student_notebook.exists()
    assert not (tmp_path / "notebooks" / f"{_EX002}.ipynb").exists()

    manifest = json.loads(
        (tmp_path / "exercises" / "migration_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["exercises"][_EX002]["layout"] == "canonical"
