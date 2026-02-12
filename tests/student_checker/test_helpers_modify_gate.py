from __future__ import annotations

from collections.abc import Callable, Mapping

EXPECTED_CHECK_CALLS = 2


def check_with_counter(
    counter: dict[str, int], *, issues: list[str] | None = None
) -> Callable[[], list[str]]:
    def _check() -> list[str]:
        counter["calls"] += 1
        return [] if issues is None else issues

    return _check


def not_started_gate(
    _notebook_path: str, exercise_no: int, _starter_baselines: Mapping[str, str]
) -> list[str]:
    return [f"Exercise {exercise_no}: NOT STARTED."]


def started_gate(
    _notebook_path: str, _exercise_no: int, _starter_baselines: Mapping[str, str]
) -> list[str]:
    return []
