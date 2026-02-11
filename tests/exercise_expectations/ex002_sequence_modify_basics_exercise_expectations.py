"""Expectations for ex002 sequence modify basics."""

from __future__ import annotations

from typing import Final

EX002_NOTEBOOK_PATH: Final[str] = "notebooks/ex002_sequence_modify_basics.ipynb"
EX002_EXPECTED_SINGLE_LINE: Final[dict[int, str]] = {
    1: "Hello Python!",
    2: "I go to Bassaleg School",
    3: "15",
    4: "Good Morning Everyone",
    5: "5.0",
    7: "The result is 100",
    8: "24",
    10: "Welcome to Python programming!",
}
EX002_EXPECTED_MULTI_LINE: Final[dict[int, list[str]]] = {
    6: ["Learning", "to", "code rocks"],
    9: ["10 minus 3 equals", "7"],
}
EX002_EXPECTED_NUMERIC: Final[dict[int, int | float]] = {
    3: int(EX002_EXPECTED_SINGLE_LINE[3]),
    5: float(EX002_EXPECTED_SINGLE_LINE[5]),
    8: int(EX002_EXPECTED_SINGLE_LINE[8]),
    9: int(EX002_EXPECTED_MULTI_LINE[9][1]),
}
EX002_EXPECTED_PRINT_CALLS: Final[dict[int, int]] = {
    4: 1,
    6: 3,
    9: 2,
}
