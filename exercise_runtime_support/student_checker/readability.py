"""Source-preserving Ruff readability analysis for notebook task cells."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, TypeGuard

from ._notebook_cells import is_source

_RULES = "E101,E111,E117,E225,E226,E227,E228,E231,E501,E741,N802,N803,N806,N816,W191,W291,W293"
_INVALID_DIAGNOSTIC_JSON = "Ruff returned invalid diagnostic JSON"


class ReadabilityToolError(RuntimeError):
    """Raised when Ruff cannot provide a valid readability result."""


@dataclass(frozen=True)
class Finding:
    """A cell-local Ruff finding."""

    code: str
    line: int
    column: int
    message: str


@dataclass(frozen=True)
class CellAnalysis:
    """Readability result for one physical notebook cell."""

    source: str
    cell_index: int
    task_tag: str
    findings: tuple[Finding, ...]
    syntax_blocked: bool


@dataclass(frozen=True)
class NotebookAnalysis:
    """Readability results for selected task cells in a notebook."""

    cells: tuple[CellAnalysis, ...]


class _DiagnosticLocation(TypedDict):
    row: int
    column: int


class _RuffDiagnostic(TypedDict):
    code: str
    location: _DiagnosticLocation
    message: str


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_diagnostic(value: object) -> TypeGuard[_RuffDiagnostic]:
    if not _is_object_dict(value):
        return False
    code = value.get("code")
    location = value.get("location")
    message = value.get("message")
    if not _is_object_dict(location):
        return False
    row = location.get("row")
    column = location.get("column")
    return (
        isinstance(code, str)
        and isinstance(row, int)
        and not isinstance(row, bool)
        and isinstance(column, int)
        and not isinstance(column, bool)
        and isinstance(message, str)
    )


def analyze_source(source: str, *, cell_index: int, task_tag: str) -> CellAnalysis:
    """Analyse one task cell's source without executing or rewriting it.

    Args:
        source: Exact source text submitted to Ruff through standard input.
        cell_index: Zero-based physical notebook cell index. Tool-error messages
            display it one-based; normal result rows identify the task without a
            physical cell number.
        task_tag: The task tag identifying this cell, such as ``"exercise1"``.

    Returns:
        The source, cell identity, Ruff findings and syntax-blocked status.

    Raises:
        ReadabilityToolError: Ruff cannot run or does not return valid
            diagnostics.
    """
    command = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--isolated",
        "--preview",
        "--no-cache",
        "--no-fix",
        "--ignore-noqa",
        "--line-length",
        "100",
        "--config",
        "indent-width=4",
        "--select",
        _RULES,
        "--output-format",
        "json",
        "--stdin-filename",
        f"{task_tag}.py",
        "-",
    ]
    try:
        result = subprocess.run(
            command,
            input=source,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
    except FileNotFoundError as error:
        raise ReadabilityToolError(f"Could not run Ruff: {error}") from error

    if result.returncode not in (0, 1) or result.stderr:
        raise ReadabilityToolError(
            f"Ruff failed for {task_tag} (cell {cell_index + 1}): {result.stderr or result.stdout}"
        )
    try:
        diagnostics: object = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ReadabilityToolError(_INVALID_DIAGNOSTIC_JSON) from error
    if not _is_object_list(diagnostics):
        raise ReadabilityToolError(_INVALID_DIAGNOSTIC_JSON)
    findings: list[Finding] = []
    for item in diagnostics:
        if not _is_diagnostic(item):
            raise ReadabilityToolError(_INVALID_DIAGNOSTIC_JSON)
        findings.append(
            Finding(
                code=item["code"],
                line=item["location"]["row"],
                column=item["location"]["column"],
                message=item["message"],
            )
        )
    return CellAnalysis(
        source=source,
        cell_index=cell_index,
        task_tag=task_tag,
        findings=tuple(findings),
        syntax_blocked=any(finding.code == "invalid-syntax" for finding in findings),
    )


def analyze_notebook(path: Path) -> NotebookAnalysis:
    """Analyse each code cell tagged with an ``exerciseN`` task tag in a notebook.

    Args:
        path: Path to the saved notebook whose tagged code cells are analysed.

    Returns:
        Results in physical notebook-cell order, preserving each selected cell's
        source and zero-based physical cell index.

    Raises:
        ReadabilityToolError: Ruff cannot run or does not return valid
            diagnostics for a selected cell.
        TypeError: A selected cell's source is neither a string nor a list of
            strings.
    """
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells: list[CellAnalysis] = []
    for cell_index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        tags = cell.get("metadata", {}).get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        task_tags = [tag for tag in tags if tag.startswith("exercise") and tag[8:].isdigit()]
        if not task_tags:
            continue
        source = cell["source"]
        if not is_source(source):
            raise TypeError("Notebook cell source must be a string or list of strings")
        cells.append(
            analyze_source(
                source if isinstance(source, str) else "".join(source),
                cell_index=cell_index,
                task_tag=task_tags[0],
            )
        )
    return NotebookAnalysis(cells=tuple(cells))
