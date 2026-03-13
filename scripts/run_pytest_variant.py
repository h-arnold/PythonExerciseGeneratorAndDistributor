"""Run pytest against the selected notebook variant."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from typing import NamedTuple

from exercise_runtime_support.execution_variant import (
    Variant,
    configure_variant_environment,
    validate_variant,
)


class ParsedArgs(NamedTuple):
    """Parsed command-line arguments."""

    variant: Variant
    pytest_args: list[str]


def parse_args(argv: Sequence[str] | None = None) -> ParsedArgs:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run pytest using the selected notebook variant.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--variant",
        choices=("student", "solution"),
        default="student",
        help="Notebook variant to expose to pytest.",
    )
    args, pytest_args = parser.parse_known_args(argv)
    return ParsedArgs(variant=validate_variant(args.variant), pytest_args=pytest_args)


def main(argv: Sequence[str] | None = None) -> int:
    """Run pytest and return its exit code."""
    args = parse_args(argv)
    env = dict(os.environ)
    configure_variant_environment(env, args.variant)
    command = [sys.executable, "-m", "pytest", *args.pytest_args]
    completed = subprocess.run(command, check=False, env=env)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
