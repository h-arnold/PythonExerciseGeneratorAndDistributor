"""Exercise-local expectations for ex002 sequence modify basics."""

from __future__ import annotations

from typing import Final

EX002_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "Hello Python!",
    2: "I go to Bassaleg School",
    3: "15",
    4: "Good Morning Everyone",
    5: "5.0",
    6: "Learning\nto\ncode rocks",
    7: "The result is 100",
    8: "24",
    9: "10 minus 3 equals\n7",
    10: "Welcome to Python programming!",
}

EX002_EXPECTED_PRINT_CALLS: Final[dict[int, int]] = {
    1: 1,
    2: 1,
    3: 1,
    4: 1,
    5: 1,
    6: 3,
    7: 1,
    8: 1,
    9: 2,
    10: 1,
}

EX002_EXPECTED_BINARY_OPERANDS: Final[dict[int, tuple[int | float, ...]]] = {
    3: (5, 3),
    5: (10, 2),
    8: (2, 3, 4),
    9: (10, 3),
}

EX002_EXPECTED_BINARY_OPERATORS: Final[dict[int, tuple[str, ...]]] = {
    3: ("*",),
    5: ("/",),
    8: ("*", "*"),
    9: ("-",),
}

EX002_ORDERED_BINARY_OPERANDS: Final[frozenset[int]] = frozenset({9})

EX002_EXPECTED_STRING_PARTS: Final[dict[int, tuple[str, ...]]] = {
    7: ("The result is ", "100"),
    10: ("Welcome", " ", "to", " ", "Python programming!"),
}
