"""Tests for source-preserving, per-task Ruff readability analysis."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

from exercise_runtime_support.student_checker import readability

_RULE_CASES = {
    "E101": ("if True:\n\t value = 1\n", "if True:\n    value = 1\n"),
    "E111": ("if True:\n  value = 1\n", "if True:\n    value = 1\n"),
    "E117": ("if True:\n        value = 1\n", "if True:\n    value = 1\n"),
    "E225": ("value=1\n", "value = 1\n"),
    "E226": ("value = 1+2\n", "value = 1 + 2\n"),
    "E227": ("value = 1<<2\n", "value = 1 << 2\n"),
    "E228": ("value = 5%2\n", "value = 5 % 2\n"),
    "E231": ("value = [1,2]\n", "value = [1, 2]\n"),
    "E501": ("value = '" + "x" * 100 + "'\n", "value = 'short'\n"),
    "E741": ("l = 1\n", "letter = 1\n"),
    "N802": ("def DoThing():\n    pass\n", "def do_thing():\n    pass\n"),
    "N803": ("def f(Arg):\n    pass\n", "def f(arg):\n    pass\n"),
    "N806": ("def f():\n    MyValue = 1\n", "def f():\n    my_value = 1\n"),
    "N816": ("myValue = 1\n", "my_value = 1\n"),
    "W191": ("if True:\n\tvalue = 1\n", "if True:\n    value = 1\n"),
    "W291": ("value = 1 \n", "value = 1\n"),
    "W293": ("value = 1\n   \n", "value = 1\n\n"),
}
_POLICY_RULES = tuple(_RULE_CASES)
_ROOT = Path(__file__).resolve().parents[2]


def _diagnostic(code: str, row: int, column: int, message: str) -> dict[str, Any]:
    return {
        "code": code,
        "location": {"row": row, "column": column},
        "message": message,
    }


def _notebook(cells: list[dict[str, Any]]) -> dict[str, Any]:
    return {"cells": cells}


def _cell(source: str | list[str], *tags: str, cell_type: str = "code") -> dict[str, Any]:
    return {
        "cell_type": cell_type,
        "metadata": {"tags": list(tags)},
        "source": source,
    }


@pytest.mark.parametrize(
    ("rule", "bad", "good"),
    [(rule, *cases) for rule, cases in _RULE_CASES.items()],
)
def test_each_selected_rule_fires_and_corrected_source_is_clean(
    rule: str, bad: str, good: str
) -> None:
    bad_results = readability.analyze_source(bad, cell_index=0, task_tag="exercise1")
    good_results = readability.analyze_source(good, cell_index=0, task_tag="exercise1")

    if rule == "E101":
        ast.parse(bad)
        assert not bad_results.syntax_blocked
    assert rule in {finding.code for finding in bad_results.findings}
    assert not good_results.findings


def test_analyser_preserves_source_and_physical_cell_and_task_identity(
    tmp_path: Path,
) -> None:
    original = _notebook(
        [
            _cell("markdown", cell_type="markdown"),
            _cell(["\n", "value=1  ", "\n"], "exercise7", "solution"),
        ]
    )
    path = tmp_path / "student.ipynb"
    path.write_text(json.dumps(original), encoding="utf-8")

    result = readability.analyze_notebook(path)

    assert len(result.cells) == 1
    analyzed = result.cells[0]
    assert analyzed.source == "\nvalue=1  \n"
    assert analyzed.cell_index == 1
    assert analyzed.task_tag == "exercise7"
    operator_finding = next(finding for finding in analyzed.findings if finding.code == "E225")
    assert (operator_finding.line, operator_finding.column) == (2, 6)
    assert json.loads(path.read_text(encoding="utf-8")) == original


@pytest.mark.parametrize("task_count", [3, 12])
def test_selects_all_exact_task_tagged_code_cells_without_task_count_limit(
    tmp_path: Path, task_count: int
) -> None:
    cells = [_cell("# starter\n", f"exercise{number}") for number in range(1, task_count + 1)]
    cells.extend(
        [
            _cell("value=1\n", "Exercise1"),
            _cell("value=1\n", "exercise_1"),
            _cell("value=1\n", "untagged-example"),
            _cell("value=1\n", "exercise20", cell_type="markdown"),
        ]
    )
    path = tmp_path / "student.ipynb"
    path.write_text(json.dumps(_notebook(cells)), encoding="utf-8")

    result = readability.analyze_notebook(path)

    expected_tags = [f"exercise{number}" for number in range(1, task_count + 1)]
    assert [cell.task_tag for cell in result.cells] == expected_tags
    assert [cell.cell_index for cell in result.cells] == list(range(task_count))


def test_task_tag_can_use_legacy_string_representation(tmp_path: Path) -> None:
    path = tmp_path / "student.ipynb"
    path.write_text(
        json.dumps(
            _notebook(
                [
                    {"cell_type": "code", "metadata": {"tags": "exercise4"}, "source": "value=1\n"},
                ]
            )
        ),
        encoding="utf-8",
    )

    result = readability.analyze_notebook(path)

    assert [(cell.cell_index, cell.task_tag) for cell in result.cells] == [(0, "exercise4")]


def test_invalid_tag_item_preserves_existing_fail_fast_error(tmp_path: Path) -> None:
    path = tmp_path / "student.ipynb"
    path.write_text(
        json.dumps(
            _notebook(
                [
                    {
                        "cell_type": "code",
                        "metadata": {"tags": ["exercise1", 1]},
                        "source": "value = 1\n",
                    }
                ]
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(AttributeError):
        readability.analyze_notebook(path)


@pytest.mark.parametrize("source", ["", "# unfinished task\n"])
def test_empty_and_comment_only_task_sources_are_analyzed(
    source: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "student.ipynb"
    path.write_text(json.dumps(_notebook([_cell(source, "exercise1")])), encoding="utf-8")
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, **kwargs})
        return subprocess.CompletedProcess(args[0], 0, "[]", "")

    monkeypatch.setattr(readability.subprocess, "run", fake_run)

    result = readability.analyze_notebook(path)

    assert len(result.cells) == 1
    assert result.cells[0].source == source
    assert result.cells[0].cell_index == 0
    assert result.cells[0].task_tag == "exercise1"
    assert not result.cells[0].findings
    assert len(calls) == 1
    assert calls[0]["input"] == source


@pytest.mark.parametrize(
    ("source", "expected_stdin"),
    [
        (" \nvalue=1  \n", " \nvalue=1  \n"),
        ([" \n", "value=1 ", " \n"], " \nvalue=1  \n"),
    ],
)
def test_source_forms_reach_ruff_exactly_and_leave_notebook_bytes_unchanged(
    source: str | list[str],
    expected_stdin: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "student.ipynb"
    path.write_text(json.dumps(_notebook([_cell(source, "exercise3")])), encoding="utf-8")
    original_bytes = path.read_bytes()
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, **kwargs})
        diagnostic = _diagnostic("E225", 2, 6, "Missing whitespace around operator")
        return subprocess.CompletedProcess(args[0], 1, json.dumps([diagnostic]), "")

    monkeypatch.setattr(readability.subprocess, "run", fake_run)

    result = readability.analyze_notebook(path)

    assert len(calls) == 1
    assert calls[0]["input"] == expected_stdin
    assert calls[0]["text"] is True
    assert result.cells[0].source == expected_stdin
    assert result.cells[0].cell_index == 0
    assert result.cells[0].task_tag == "exercise3"
    finding = next(finding for finding in result.cells[0].findings if finding.code == "E225")
    assert (finding.line, finding.column) == (2, 6)
    assert path.read_bytes() == original_bytes


def test_analyzes_saved_edits_afresh_and_does_not_create_source_files(tmp_path: Path) -> None:
    path = tmp_path / "student.ipynb"
    original = _notebook([_cell("value=1\n", "exercise1")])
    path.write_text(json.dumps(original), encoding="utf-8")

    first = readability.analyze_notebook(path)
    edited = _notebook([_cell("value = 1\n", "exercise1")])
    path.write_text(json.dumps(edited), encoding="utf-8")
    second = readability.analyze_notebook(path)

    assert first.cells[0].findings
    assert not second.cells[0].findings
    assert list(tmp_path.iterdir()) == [path]


def test_runs_one_isolated_stdin_process_per_cell_and_continues_after_syntax_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "student.ipynb"
    sources = ["if True\n", "value=1\n"]
    path.write_text(
        json.dumps(_notebook([_cell(sources[0], "exercise1"), _cell(sources[1], "exercise2")])),
        encoding="utf-8",
    )
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, **kwargs})
        if len(calls) == 1:
            output = json.dumps([_diagnostic("invalid-syntax", 1, 1, "Expected ':'")])
            return subprocess.CompletedProcess(args[0], 1, output, "")
        output = json.dumps([_diagnostic("E225", 1, 6, "Missing whitespace around operator")])
        return subprocess.CompletedProcess(args[0], 1, output, "")

    monkeypatch.setattr(readability.subprocess, "run", fake_run)
    result = readability.analyze_notebook(path)

    assert len(calls) == len(sources)
    assert [call["input"] for call in calls] == sources
    assert all(call["shell"] is False for call in calls)
    assert all(isinstance(call["args"][0], list) for call in calls)
    argv = calls[0]["args"][0]
    assert argv[:3] == [sys.executable, "-m", "ruff"]
    assert "check" in argv
    assert "--isolated" in argv
    assert "--preview" in argv
    assert "--no-cache" in argv
    assert "--no-fix" in argv
    assert "--ignore-noqa" in argv
    assert argv[argv.index("--line-length") + 1] == "100"
    config_values = [
        argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "--config"
    ]
    assert "indent-width=4" in config_values
    assert set(argv[argv.index("--select") + 1].split(",")) == set(_POLICY_RULES)
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--stdin-filename") + 1].endswith(".py")
    assert argv[-1] == "-"
    assert all(call["text"] is True for call in calls)
    assert result.cells[0].syntax_blocked
    assert result.cells[1].cell_index == 1
    assert result.cells[1].findings[0].code == "E225"
    assert not list(tmp_path.glob("*.py"))


def test_importing_analyser_does_not_launch_ruff() -> None:
    code = (
        "import subprocess\n"
        "def fail(*args, **kwargs):\n"
        "    raise AssertionError('subprocess launched during import')\n"
        "subprocess.run = fail\n"
        "import exercise_runtime_support.student_checker.readability\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_ROOT,
        env={**os.environ, "PYTHONPATH": str(_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_source_is_not_executed(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.append(kwargs["input"])
        return subprocess.CompletedProcess(args[0], 0, "[]", "")

    monkeypatch.setattr(readability.subprocess, "run", fake_run)
    source = "raise RuntimeError('must not execute')\n"

    readability.analyze_source(source, cell_index=0, task_tag="exercise1")

    assert captured == [source]


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr"),
    [
        (0, "[]", ""),
        (1, json.dumps([_diagnostic("E225", 1, 6, "Missing whitespace")]), ""),
        (2, "", "invalid configuration"),
        (0, "not json", ""),
        (0, "[]", "warning: selected rules have no effect"),
    ],
)
def test_tool_result_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    returncode: int,
    stdout: str,
    stderr: str,
) -> None:
    path = tmp_path / "student.ipynb"
    path.write_text(json.dumps(_notebook([_cell("value = 1\n", "exercise1")])), encoding="utf-8")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], returncode, stdout, stderr)

    monkeypatch.setattr(readability.subprocess, "run", fake_run)

    if returncode > 1 or stdout == "not json" or stderr:
        with pytest.raises(readability.ReadabilityToolError):
            readability.analyze_notebook(path)
    else:
        result = readability.analyze_notebook(path)
        assert bool(result.cells[0].findings) is (returncode == 1)


@pytest.mark.parametrize(
    "diagnostics",
    [
        ["oops"],
        [{"code": "E225"}],
        [
            {
                "code": 225,
                "location": {"row": 1, "column": 1},
                "message": "Missing whitespace",
            }
        ],
        [
            {
                "code": "E225",
                "location": {"row": "second", "column": 1},
                "message": "Missing whitespace",
            }
        ],
        [
            {
                "code": "E225",
                "location": {"row": 1, "column": "first"},
                "message": "Missing whitespace",
            }
        ],
        [
            {
                "code": "E225",
                "location": {"row": 1, "column": 1},
                "message": 123,
            }
        ],
    ],
)
def test_malformed_diagnostic_records_raise_tool_error(
    diagnostics: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], 1, json.dumps(diagnostics), "")

    monkeypatch.setattr(readability.subprocess, "run", fake_run)

    with pytest.raises(readability.ReadabilityToolError):
        readability.analyze_source("value=1\n", cell_index=0, task_tag="exercise1")


def test_missing_ruff_module_result_is_a_tool_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "student.ipynb"
    path.write_text(json.dumps(_notebook([_cell("value = 1\n", "exercise1")])), encoding="utf-8")

    def missing_module_result(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], 1, "", "/python: No module named ruff")

    monkeypatch.setattr(readability.subprocess, "run", missing_module_result)
    with pytest.raises(readability.ReadabilityToolError, match="No module named ruff"):
        readability.analyze_notebook(path)


def test_missing_interpreter_is_a_tool_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_interpreter(*args: Any, **kwargs: Any) -> None:
        raise FileNotFoundError("python interpreter")

    monkeypatch.setattr(readability.subprocess, "run", missing_interpreter)
    with pytest.raises(readability.ReadabilityToolError, match="python interpreter"):
        readability.analyze_source("value = 1\n", cell_index=0, task_tag="exercise1")


def test_tool_error_uses_one_based_cell_reference(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "student.ipynb"
    path.write_text(
        json.dumps(
            _notebook(
                [
                    _cell("markdown", cell_type="markdown"),
                    _cell("value = 1\n", "exercise1"),
                ]
            )
        ),
        encoding="utf-8",
    )

    def tool_failure(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], 2, "", "invalid configuration")

    monkeypatch.setattr(readability.subprocess, "run", tool_failure)
    with pytest.raises(readability.ReadabilityToolError, match=r"cell 2"):
        readability.analyze_notebook(path)


def test_source_and_dev_extra_and_template_pin_ruff_exactly() -> None:
    source_project = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    template_project = tomllib.loads(
        (_ROOT / "template_repo_files/pyproject.toml").read_text(encoding="utf-8")
    )
    lock = tomllib.loads((_ROOT / "uv.lock").read_text(encoding="utf-8"))
    lock_ruff = next(package for package in lock["package"] if package["name"] == "ruff")

    project_ruff = next(
        dep for dep in source_project["project"]["dependencies"] if dep.lower().startswith("ruff")
    )
    dev_ruff = next(
        dep
        for dep in source_project["project"]["optional-dependencies"]["dev"]
        if dep.lower().startswith("ruff")
    )
    template_ruff = next(
        dep for dep in template_project["project"]["dependencies"] if dep.lower().startswith("ruff")
    )
    assert project_ruff == "ruff==0.14.13"
    assert dev_ruff == "ruff==0.14.13"
    assert template_ruff == "ruff==0.14.13"
    assert lock_ruff["version"] == "0.14.13"
