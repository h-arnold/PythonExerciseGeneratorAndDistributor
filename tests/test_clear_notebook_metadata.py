"""Tests for the notebook metadata cleaning helper."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.clear_notebook_metadata import clear_notebook_metadata, main


def _write_notebook(path: Path, metadata: object | None) -> Path:
    data = {
        "metadata": metadata,
        "cells": [],
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return path


def test_clear_metadata_removes_existing(tmp_path: Path) -> None:
    notebook = _write_notebook(tmp_path / "run.ipynb", {"kernelspec": {"name": "python"}})
    assert clear_notebook_metadata(notebook)
    content = json.loads(notebook.read_text(encoding="utf-8"))
    assert content["metadata"] == {}


def test_clear_metadata_skips_clean(tmp_path: Path) -> None:
    notebook = _write_notebook(tmp_path / "clean.ipynb", {})
    assert not clear_notebook_metadata(notebook)


def test_main_detects_updates_in_directory(tmp_path: Path) -> None:
    notebooks = tmp_path / "notebooks"
    notebooks.mkdir()
    note = _write_notebook(notebooks / "lesson.ipynb", {"metadata": "should go"})
    result = main(["--paths", str(notebooks)])
    assert result == 1
    assert json.loads(note.read_text(encoding="utf-8"))["metadata"] == {}


def test_main_returns_zero_when_nothing_changes(tmp_path: Path) -> None:
    notebooks = tmp_path / "notebooks"
    notebooks.mkdir()
    _write_notebook(notebooks / "lesson.ipynb", {})
    assert main(["--paths", str(notebooks)]) == 0
