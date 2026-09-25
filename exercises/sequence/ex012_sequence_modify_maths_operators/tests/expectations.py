"""Canonical expectations for ex012 sequence modify maths operators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Ex012RequiredOperation:
    """A live assignment required by one exercise part."""

    target: str
    operator: str
    operands: tuple[str | int | float, str | int | float]
    round_places: int | None = None


@dataclass(frozen=True)
class Ex012OldAssignment:
    """A placeholder assignment that must be removed from a target variable."""

    target: str
    value: str | int | float


@dataclass(frozen=True)
class Ex012OldExpression:
    """A starter expression that must not remain anywhere in the tagged cell."""

    target: str
    operator: str
    operands: tuple[str | int | float, str | int | float]


EX012_EXPECTED_OUTPUTS: Final[dict[int, str]] = {
    1: "Full groups: 7",
    2: "Leftover cupcakes: 1",
    3: "Complete teams: 4",
    4: "Leftover stickers: 5",
    5: "Average points: 6.7",
    6: "Total cost: £3.77",
    7: "125 minutes is 2 hours and 5 minutes",
    8: "389p is £3 and 89p",
    9: "Average speed: 43.1 km/h",
    10: "Full boxes: 6\nLeftover crayons: 2\nPrice per box: £1.83",
}

# Only these arithmetic operators are part of the corrected task or its
# straight-line string construction.  In particular, subtraction is never a
# corrected result, while the operators listed for each task remain valid.
EX012_ALLOWED_OPERATORS: Final[dict[int, frozenset[str]]] = {
    1: frozenset({"//", "+"}),
    2: frozenset({"%", "+"}),
    3: frozenset({"//", "+"}),
    4: frozenset({"%", "+"}),
    5: frozenset({"/", "+"}),
    6: frozenset({"*", "+"}),
    7: frozenset({"//", "%", "+"}),
    8: frozenset({"//", "%", "+"}),
    9: frozenset({"/", "+"}),
    10: frozenset({"//", "%", "/", "+"}),
}

EX012_ALLOWED_CALLS: Final[dict[int, frozenset[str]]] = {
    1: frozenset({"print", "str"}),
    2: frozenset({"print", "str"}),
    3: frozenset({"print", "str"}),
    4: frozenset({"print", "str"}),
    5: frozenset({"print", "str", "round"}),
    6: frozenset({"print", "str", "round"}),
    7: frozenset({"print", "str"}),
    8: frozenset({"print", "str"}),
    9: frozenset({"print", "str", "round"}),
    10: frozenset({"print", "str", "round"}),
}

# Each operation names the result that must be bound before the corresponding
# positional print payload.  A non-None round_places means that the live
# binding is a round call whose value still contains the named operation.
EX012_REQUIRED_OPERATIONS: Final[dict[int, tuple[Ex012RequiredOperation, ...]]] = {
    1: (Ex012RequiredOperation("full_groups", "//", ("students", "group_size")),),
    2: (Ex012RequiredOperation("leftover", "%", ("cupcakes", "per_box")),),
    3: (Ex012RequiredOperation("complete_teams", "//", ("players", "team_size")),),
    4: (Ex012RequiredOperation("leftover", "%", ("stickers", "stickers_per_sheet")),),
    5: (Ex012RequiredOperation("average_points", "/", ("total_points", "games"), round_places=1),),
    6: (Ex012RequiredOperation("total", "*", ("price", "amount"), round_places=2),),
    7: (
        Ex012RequiredOperation("hours", "//", ("minutes", 60)),
        Ex012RequiredOperation("minutes_left", "%", ("minutes", 60)),
    ),
    8: (
        Ex012RequiredOperation("pounds", "//", ("pence", 100)),
        Ex012RequiredOperation("leftover_pence", "%", ("pence", 100)),
    ),
    9: (Ex012RequiredOperation("speed", "/", ("distance", "time_hours"), round_places=1),),
    10: (
        Ex012RequiredOperation("full_boxes", "//", ("crayons", "per_box")),
        Ex012RequiredOperation("leftover", "%", ("crayons", "per_box")),
        Ex012RequiredOperation("price_per_box", "/", ("total_price", "full_boxes"), round_places=2),
    ),
}

# Each inner tuple is the corrected target(s) used by one top-level print call.
EX012_EXPECTED_PRINT_TARGETS: Final[dict[int, tuple[tuple[str, ...], ...]]] = {
    1: (("full_groups",),),
    2: (("leftover",),),
    3: (("complete_teams",),),
    4: (("leftover",),),
    5: (("average_points",),),
    6: (("total",),),
    7: (("hours", "minutes_left"),),
    8: (("pounds", "leftover_pence"),),
    9: (("speed",),),
    10: (("full_boxes",), ("leftover",), ("price_per_box",)),
}

# These values are part of the supplied scenarios.  Keeping them fixed makes
# an otherwise-correct operation from a different problem insufficient.
EX012_REQUIRED_LITERALS: Final[dict[int, dict[str, int | float]]] = {
    1: {"students": 29, "group_size": 4},
    2: {"cupcakes": 29, "per_box": 4},
    3: {"players": 23, "team_size": 5},
    4: {"stickers": 23, "stickers_per_sheet": 6},
    5: {"total_points": 20, "games": 3},
    6: {"price": 1.257, "amount": 3},
    7: {"minutes": 125},
    8: {"pence": 389},
    9: {"distance": 86.25, "time_hours": 2},
    10: {"crayons": 26, "per_box": 4, "total_price": 10.99},
}

# These are deliberately conflict-specific.  A division or multiplication that
# is genuinely required by a task (for example / in exercises 5, 9, and 10) is
# not treated as an old operator merely because it appears in the cell.
EX012_OLD_ASSIGNMENTS: Final[dict[int, tuple[Ex012OldAssignment, ...]]] = {
    2: (Ex012OldAssignment("leftover", 0),),
    4: (Ex012OldAssignment("leftover", 0),),
    8: (Ex012OldAssignment("leftover_pence", 0),),
}

EX012_OLD_EXPRESSIONS: Final[dict[int, tuple[Ex012OldExpression, ...]]] = {
    1: (Ex012OldExpression("full_groups", "/", ("students", "group_size")),),
    3: (Ex012OldExpression("complete_teams", "/", ("players", "team_size")),),
    7: (
        Ex012OldExpression("hours", "/", ("minutes", 60)),
        Ex012OldExpression("minutes_left", "-", ("minutes", 60)),
    ),
    8: (Ex012OldExpression("pounds", "/", ("pence", 100)),),
    10: (
        Ex012OldExpression("full_boxes", "/", ("crayons", "per_box")),
        Ex012OldExpression("leftover", "-", ("crayons", "per_box")),
    ),
}
