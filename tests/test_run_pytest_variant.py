from __future__ import annotations

from scripts.run_pytest_variant import parse_args


def test_parse_args_collects_pytest_flags_without_double_dash() -> None:
    args = parse_args(["--variant", "solution", "-q", "tests/test_ex001_sanity.py"])

    assert args.variant == "solution"
    assert args.pytest_args == ["-q", "tests/test_ex001_sanity.py"]
