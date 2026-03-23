from __future__ import annotations

import subprocess

import pytest

from scripts.run_pytest_variant import main, parse_args


def test_parse_args_collects_pytest_flags_without_double_dash() -> None:
    args = parse_args(
        [
            "--variant",
            "solution",
            "-q",
            "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py",
        ]
    )

    assert args.variant == "solution"
    assert args.pytest_args == [
        "-q",
        "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py",
    ]


def test_main_passes_explicit_variant_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_env: dict[str, str] = {}

    def fake_run(
        command: list[str],
        *,
        check: bool,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        assert command[-1] == (
            "exercises/sequence/ex002_sequence_modify_basics/tests/"
            "test_ex002_sequence_modify_basics.py"
        )
        assert check is False
        captured_env.update(env)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("scripts.run_pytest_variant.subprocess.run", fake_run)

    exit_code = main(
        [
            "--variant",
            "solution",
            "exercises/sequence/ex002_sequence_modify_basics/tests/test_ex002_sequence_modify_basics.py",
        ]
    )

    assert exit_code == 0
    assert captured_env["PYTUTOR_ACTIVE_VARIANT"] == "solution"
