from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

pytest_plugins = ("pytester",)

PLUGIN_PATH = Path(__file__).with_name("autograde_plugin.py")
RESULTS_FILENAME = "results.json"
TASK_NUMBER = 7
TWO_TEST_MAX_SCORE = 2.0
TRUNCATED_MESSAGE_LIMIT = 1000
EXPECTED_ASSERT_LINE = 2


@pytest.fixture(autouse=True)
def _register_autograde_plugin(pytester: pytest.Pytester) -> None:
    pytester.syspathinsert(str(PLUGIN_PATH.parent))
    pytester.makeconftest("pytest_plugins = ['autograde_plugin']\n")


def _write_test_module(
    pytester: pytest.Pytester, body: str, *, name: str = "test_autograde"
) -> None:
    pytester.makepyfile(**{name: textwrap.dedent(body)})


def _run_with_results(
    pytester: pytest.Pytester,
    *,
    results_path: str | Path = RESULTS_FILENAME,
    args: list[str] | None = None,
) -> tuple[pytest.RunResult, dict[str, object], Path]:
    path_arg = str(results_path)
    extra_args = [f"--autograde-results-path={path_arg}"]
    if args:
        extra_args.extend(args)
    result = pytester.runpytest(*extra_args)
    json_path = pytester.path / path_arg
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return result, data, json_path


def test_plugin_captures_passing_test(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_example() -> None:
            assert 1 == 1
        """,
    )
    result, payload, _ = _run_with_results(pytester)
    result.assert_outcomes(passed=1)
    assert payload["score"] == 1.0
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["status"] == "pass"
    assert test_entry["score"] == 1.0
    assert test_entry["message"] is None


def test_plugin_captures_failing_test(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_failure() -> None:
            assert 1 == 0
        """,
    )
    result, payload, _ = _run_with_results(pytester)
    result.assert_outcomes(failed=1)
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["status"] == "fail"
    assert test_entry["score"] == 0.0
    assert "1 == 0" in test_entry["message"]


def test_plugin_captures_error_test(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        import pytest

        @pytest.fixture(autouse=True)
        def broken() -> None:
            raise RuntimeError("boom")

        def test_error() -> None:
            pass
        """,
    )
    result, payload, _ = _run_with_results(pytester)
    result.assert_outcomes(errors=1)
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["status"] == "error"
    assert test_entry["score"] == 0.0
    assert "RuntimeError" in test_entry["message"]


def test_plugin_extracts_task_number(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        import pytest

        @pytest.mark.task(taskno=7)
        def test_marked() -> None:
            assert True
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["taskno"] == TASK_NUMBER


def test_plugin_handles_missing_task_marker(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_unmarked() -> None:
            assert True
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["taskno"] is None


def test_plugin_extracts_name_from_marker(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        import pytest

        @pytest.mark.task(taskno=1, name="Custom Task")
        def test_named_marker() -> None:
            assert True
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["name"] == "Custom Task"


def test_plugin_extracts_name_from_docstring(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        '''\
        def test_docstring() -> None:
            """Docstring summary."""
            assert True
        ''',
    )
    _, payload, _ = _run_with_results(pytester)
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["name"] == "Docstring summary."


def test_plugin_extracts_name_from_nodeid(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_simple_case() -> None:
            assert True
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    test_entry = payload["tests"][0]  # type: ignore[index]
    assert test_entry["name"] == "simple case"


def test_plugin_writes_valid_json(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_json() -> None:
            assert True
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    assert payload["status"] == "pass"
    assert payload["max_score"] == 1.0
    assert isinstance(payload["tests"], list)


def test_plugin_creates_output_directory(pytester: pytest.Pytester) -> None:
    results_path = Path("nested") / "dir" / "results.json"
    _write_test_module(
        pytester,
        """\
        def test_directory_creation() -> None:
            assert True
        """,
    )
    _, payload, json_path = _run_with_results(pytester, results_path=results_path)
    assert payload["status"] == "pass"
    assert json_path.is_file()


def test_plugin_handles_write_errors(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = pytester.path / RESULTS_FILENAME
    original_open = Path.open
    call_count = {"count": 0}

    # type: ignore[override]
    def _fail_once(self: Path, *args: object, **kwargs: object):
        if self == target and call_count["count"] == 0:
            call_count["count"] += 1
            raise OSError("disk full")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", _fail_once, raising=True)

    _write_test_module(
        pytester,
        """\
        def test_write_error() -> None:
            assert True
        """,
    )
    result, payload, _ = _run_with_results(pytester)
    result.assert_outcomes(passed=1)
    assert payload == {
        "status": "error",
        "score": 0.0,
        "max_score": 0.0,
        "tests": [],
    }
    stdout = result.stdout.str()
    assert "Autograde error: Failed to write autograde results" in stdout


def test_plugin_calculates_max_score(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_one() -> None:
            assert True

        def test_two() -> None:
            assert False
        """,
    )
    result, payload, _ = _run_with_results(pytester)
    result.assert_outcomes(passed=1, failed=1)
    assert payload["max_score"] == TWO_TEST_MAX_SCORE


def test_plugin_calculates_overall_status_pass(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_all_good() -> None:
            assert True
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    assert payload["status"] == "pass"


def test_plugin_calculates_overall_status_fail(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_first() -> None:
            assert True

        def test_second() -> None:
            assert False
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    assert payload["status"] == "fail"


def test_plugin_calculates_overall_status_error(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        import pytest

        @pytest.fixture(autouse=True)
        def broken() -> None:
            raise RuntimeError("failure")

        def test_problem() -> None:
            pass
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    assert payload["status"] == "error"


def test_plugin_truncates_long_messages(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_long_message() -> None:
            raise AssertionError("x" * 1500)
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    message = payload["tests"][0]["message"]  # type: ignore[index]
    assert isinstance(message, str)
    assert len(message) == TRUNCATED_MESSAGE_LIMIT
    assert message.endswith("...")


def test_plugin_extracts_line_numbers(pytester: pytest.Pytester) -> None:
    _write_test_module(
        pytester,
        """\
        def test_line_numbers() -> None:
            assert 2 == 1
        """,
    )
    _, payload, _ = _run_with_results(pytester)
    line_no = payload["tests"][0]["line_no"]  # type: ignore[index]
    assert line_no == EXPECTED_ASSERT_LINE
