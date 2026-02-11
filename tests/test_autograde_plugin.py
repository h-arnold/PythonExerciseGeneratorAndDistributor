from __future__ import annotations

import json
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import IO, Any, NotRequired, Protocol, TypedDict, cast

import pytest
from pytest import approx  # pyright: ignore[reportUnknownVariableType]

pytest_plugins = ("pytester",)

PLUGIN_PATH = Path(__file__).with_name("autograde_plugin.py")
RESULTS_FILENAME = "results.json"
TASK_NUMBER = 7
TWO_TEST_MAX_SCORE = 2.0
TRUNCATED_MESSAGE_LIMIT = 1000
EXPECTED_ASSERT_LINE = 2


def _register_autograde_plugin(
    pytester: pytest.Pytester,
) -> None:
    pytester.syspathinsert(str(PLUGIN_PATH.parent))
    pytester.makeconftest("pytest_plugins = ['autograde_plugin']\n")


_register_autograde_plugin = pytest.fixture(autouse=True)(_register_autograde_plugin)


def _write_test_module(
    pytester: pytest.Pytester, body: str, *, name: str = "test_autograde"
) -> None:
    pytester.makepyfile(**{name: textwrap.dedent(body)})  # pyright: ignore[reportUnknownMemberType]


class AutogradePayloadTestEntry(TypedDict):
    nodeid: str
    name: str
    taskno: int | None
    status: str
    score: float
    message: str | None
    line_no: int | None
    duration: float | None
    stdout: NotRequired[str]
    stderr: NotRequired[str]
    log: NotRequired[str]
    extra: NotRequired[dict[str, Any]]


class AutogradePayload(TypedDict):
    status: str
    score: float
    max_score: float
    tests: list[AutogradePayloadTestEntry]
    start_timestamp: NotRequired[float | None]
    end_timestamp: NotRequired[float | None]
    errors: NotRequired[list[str]]
    notes: NotRequired[list[str]]


class RunWithResults(Protocol):
    def __call__(
        self,
        *,
        results_path: str | Path = RESULTS_FILENAME,
        args: Sequence[str] | None = None,
    ) -> tuple[pytest.RunResult, AutogradePayload, Path]: ...


class ExpectedTestFields(TypedDict, total=False):
    message: str | None
    taskno: int | None
    name: str


def _assert_dict(value: object, *, context: str) -> dict[str, Any]:
    assert isinstance(value, dict), f"{context} should be a dict"
    return cast(dict[str, Any], value)


def _assert_autograde_test_entry(value: object) -> AutogradePayloadTestEntry:
    entry = _assert_dict(value, context="Test entry")
    required_keys = (
        "nodeid",
        "name",
        "status",
        "score",
        "message",
        "line_no",
        "duration",
        "taskno",
    )
    for key in required_keys:
        assert key in entry, f"Missing required test field: {key}"

    assert isinstance(entry["nodeid"], str)
    assert isinstance(entry["name"], str)
    assert isinstance(entry["status"], str)
    assert isinstance(entry["score"], (int, float))

    message = entry["message"]
    line_no = entry["line_no"]
    duration = entry["duration"]
    taskno = entry["taskno"]

    assert isinstance(message, str) or message is None
    assert isinstance(line_no, int) or line_no is None
    assert isinstance(duration, (int, float)) or duration is None
    assert isinstance(taskno, int) or taskno is None
    return cast(AutogradePayloadTestEntry, entry)


def _assert_autograde_payload(value: object) -> AutogradePayload:
    payload = _assert_dict(value, context="Autograde payload")
    for key in ("status", "score", "max_score", "tests"):
        assert key in payload, f"Missing required payload field: {key}"

    assert isinstance(payload["status"], str)
    assert isinstance(payload["score"], (int, float))
    assert isinstance(payload["max_score"], (int, float))

    tests = payload["tests"]
    assert isinstance(tests, list)
    tests_list = cast(list[object], tests)
    for test in tests_list:
        _assert_autograde_test_entry(test)

    for key in ("start_timestamp", "end_timestamp"):
        if key in payload:
            assert payload[key] is None or isinstance(payload[key], (int, float))
    for key in ("errors", "notes"):
        if key in payload:
            assert isinstance(payload[key], list)

    return cast(AutogradePayload, payload)


def expect_single_test_entry(
    payload: AutogradePayload,
    *,
    status: str,
    score: float,
    expected: ExpectedTestFields | None = None,
) -> AutogradePayloadTestEntry:
    tests = payload["tests"]
    assert len(tests) == 1, f"Expected a single test entry, received {len(tests)}"
    entry_candidate = tests[0]
    entry = _assert_autograde_test_entry(entry_candidate)
    assert entry["status"] == status
    assert entry["score"] == approx(score)
    if expected:
        if "message" in expected:
            assert entry["message"] == expected["message"]
        if "taskno" in expected:
            assert entry["taskno"] == expected["taskno"]
        if "name" in expected:
            assert entry["name"] == expected["name"]
    return entry


def _load_payload(json_path: Path) -> AutogradePayload:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return _assert_autograde_payload(data)


@pytest.fixture
def run_with_results(pytester: pytest.Pytester) -> RunWithResults:
    def _runner(
        *,
        results_path: str | Path = RESULTS_FILENAME,
        args: Sequence[str] | None = None,
    ) -> tuple[pytest.RunResult, AutogradePayload, Path]:
        path_arg = str(results_path)
        extra_args = [f"--autograde-results-path={path_arg}"]
        if args:
            extra_args.extend(args)
        result = pytester.runpytest(*extra_args)
        json_path = pytester.path / path_arg
        payload = _load_payload(json_path)
        return result, payload, json_path

    return _runner


def test_plugin_captures_passing_test(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_example() -> None:
            assert 1 == 1
        """,
    )
    result, payload, _ = run_with_results()
    result.assert_outcomes(passed=1)
    assert payload["score"] == 1.0
    test_entry = expect_single_test_entry(
        payload,
        status="pass",
        score=1.0,
        expected={"message": None},
    )
    assert test_entry["name"]


def test_plugin_captures_failing_test(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_failure() -> None:
            assert 1 == 0
        """,
    )
    result, payload, _ = run_with_results()
    result.assert_outcomes(failed=1)
    test_entry = expect_single_test_entry(
        payload,
        status="fail",
        score=0.0,
    )
    assert test_entry["message"] is not None
    assert "1 == 0" in test_entry["message"]


def test_plugin_captures_error_test(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
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
    result, payload, _ = run_with_results()
    result.assert_outcomes(errors=1)
    test_entry = expect_single_test_entry(
        payload,
        status="error",
        score=0.0,
    )
    assert test_entry["message"] is not None
    assert "RuntimeError" in test_entry["message"]


def test_plugin_extracts_task_number(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        import pytest

        @pytest.mark.task(taskno=7)
        def test_marked() -> None:
            assert True
        """,
    )
    _, payload, _ = run_with_results()
    expect_single_test_entry(
        payload,
        status="pass",
        score=1.0,
        expected={"taskno": TASK_NUMBER},
    )


def test_plugin_handles_missing_task_marker(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_unmarked() -> None:
            assert True
        """,
    )
    _, payload, _ = run_with_results()
    expect_single_test_entry(
        payload,
        status="pass",
        score=1.0,
        expected={"taskno": None},
    )


def test_plugin_extracts_name_from_marker(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        import pytest

        @pytest.mark.task(taskno=1, name="Custom Task")
        def test_named_marker() -> None:
            assert True
        """,
    )
    _, payload, _ = run_with_results()
    expect_single_test_entry(
        payload,
        status="pass",
        score=1.0,
        expected={"name": "Custom Task"},
    )


def test_plugin_extracts_name_from_docstring(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        '''\
        def test_docstring() -> None:
            """Docstring summary."""
            assert True
        ''',
    )
    _, payload, _ = run_with_results()
    expect_single_test_entry(
        payload,
        status="pass",
        score=1.0,
        expected={"name": "Docstring summary."},
    )


def test_plugin_extracts_name_from_nodeid(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_simple_case() -> None:
            assert True
        """,
    )
    _, payload, _ = run_with_results()
    expect_single_test_entry(
        payload,
        status="pass",
        score=1.0,
        expected={"name": "simple case"},
    )


def test_plugin_writes_valid_json(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_json() -> None:
            assert True
        """,
    )
    _, payload, _ = run_with_results()
    assert payload["status"] == "pass"
    assert payload["max_score"] == 1.0
    assert isinstance(payload["tests"], list)


def test_plugin_creates_output_directory(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    results_path = Path("nested") / "dir" / "results.json"
    _write_test_module(
        pytester,
        """\
        def test_directory_creation() -> None:
            assert True
        """,
    )
    _, payload, json_path = run_with_results(results_path=results_path)
    assert payload["status"] == "pass"
    assert json_path.is_file()


def test_plugin_handles_write_errors(
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
    run_with_results: RunWithResults,
) -> None:
    target = pytester.path / RESULTS_FILENAME
    original_open = Path.open
    call_count = {"count": 0}

    # type: ignore[override]
    def _fail_once(self: Path, *args: Any, **kwargs: Any) -> IO[Any]:  # pyright: ignore[reportUnknownVariableType]
        if self == target and call_count["count"] == 0:
            call_count["count"] += 1
            raise OSError("disk full")
        return original_open(self, *args, **kwargs)  # pyright: ignore[reportUnknownVariableType]

    monkeypatch.setattr(Path, "open", _fail_once, raising=True)

    _write_test_module(
        pytester,
        """\
        def test_write_error() -> None:
            assert True
        """,
    )
    result, payload, _ = run_with_results()
    result.assert_outcomes(passed=1)
    assert payload == {
        "status": "error",
        "score": 0.0,
        "max_score": 0.0,
        "tests": [],
    }
    stdout = result.stdout.str()
    assert "Autograde error: Failed to write autograde results" in stdout


def test_plugin_calculates_max_score(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_one() -> None:
            assert True

        def test_two() -> None:
            assert False
        """,
    )
    result, payload, _ = run_with_results()
    result.assert_outcomes(passed=1, failed=1)
    assert payload["max_score"] == TWO_TEST_MAX_SCORE


def test_plugin_calculates_overall_status_pass(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_all_good() -> None:
            assert True
        """,
    )
    _, payload, _ = run_with_results()
    assert payload["status"] == "pass"


def test_plugin_calculates_overall_status_fail(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_first() -> None:
            assert True

        def test_second() -> None:
            assert False
        """,
    )
    _, payload, _ = run_with_results()
    assert payload["status"] == "fail"


def test_plugin_calculates_overall_status_error(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
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
    _, payload, _ = run_with_results()
    assert payload["status"] == "error"


def test_plugin_truncates_long_messages(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_long_message() -> None:
            raise AssertionError("x" * 1500)
        """,
    )
    _, payload, _ = run_with_results()
    entry = expect_single_test_entry(
        payload,
        status="fail",
        score=0.0,
    )
    message = entry["message"]
    assert isinstance(message, str)
    assert len(message) == TRUNCATED_MESSAGE_LIMIT
    assert message.endswith("...")


def test_plugin_extracts_line_numbers(
    pytester: pytest.Pytester, run_with_results: RunWithResults
) -> None:
    _write_test_module(
        pytester,
        """\
        def test_line_numbers() -> None:
            assert 2 == 1
        """,
    )
    _, payload, _ = run_with_results()
    entry = expect_single_test_entry(
        payload,
        status="fail",
        score=0.0,
    )
    assert entry["line_no"] == EXPECTED_ASSERT_LINE
