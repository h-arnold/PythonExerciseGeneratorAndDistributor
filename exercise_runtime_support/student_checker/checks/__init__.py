"""Generic check entry points backed by exercise-local test support modules."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any, Final, NamedTuple, TypeVar

from exercise_runtime_support.exercise_catalogue import get_catalogue_key_for_exercise_id
from exercise_runtime_support.exercise_test_support import load_exercise_test_module
from exercise_runtime_support.notebook_grader import NotebookGradingError

from ..models import Ex002CheckResult, Ex006CheckResult, ExerciseCheckResult
from .base import Ex006CheckDefinition, ExerciseCheckDefinition


def _load_ex002_checks() -> list[Any]:
    module = load_exercise_test_module(
        get_catalogue_key_for_exercise_id(2),
        "framework_support",
    )
    return list(module.EX002_CHECKS)


def _load_check_list(exercise_id: int) -> list[Any]:
    module = load_exercise_test_module(
        get_catalogue_key_for_exercise_id(exercise_id),
        "student_checker_support",
    )
    return list(module.CHECKS)


_EX003_CHECKS = _load_check_list(3)
EX003_CHECKS = _EX003_CHECKS
_EX004_CHECKS = _load_check_list(4)
EX004_CHECKS = _EX004_CHECKS
_EX005_CHECKS = _load_check_list(5)
EX005_CHECKS = _EX005_CHECKS
_EX006_CHECKS = _load_check_list(6)
EX006_CHECKS = _EX006_CHECKS
_EX007_CHECKS = _load_check_list(7)
EX007_CHECKS = _EX007_CHECKS

__all__ = [
    "EX003_CHECKS",
    "EX004_CHECKS",
    "EX005_CHECKS",
    "EX006_CHECKS",
    "EX007_CHECKS",
    "Ex006CheckDefinition",
    "ExerciseCheckDefinition",
    "check_ex002_summary",
    "check_ex003",
    "check_ex004",
    "check_ex005",
    "check_ex006",
    "check_ex007",
    "run_ex002_checks",
    "run_ex003_checks",
    "run_ex004_checks",
    "run_ex005_checks",
    "run_ex006_checks",
    "run_ex007_checks",
]


class _CheckListBinding(NamedTuple):
    private_attr: str
    public_attr: str


_CHECK_LIST_BINDINGS: Final[dict[str, _CheckListBinding]] = {
    "EX003_CHECKS": _CheckListBinding(
        private_attr="_EX003_CHECKS",
        public_attr="EX003_CHECKS",
    ),
    "EX004_CHECKS": _CheckListBinding(
        private_attr="_EX004_CHECKS",
        public_attr="EX004_CHECKS",
    ),
    "EX005_CHECKS": _CheckListBinding(
        private_attr="_EX005_CHECKS",
        public_attr="EX005_CHECKS",
    ),
    "EX006_CHECKS": _CheckListBinding(
        private_attr="_EX006_CHECKS",
        public_attr="EX006_CHECKS",
    ),
    "EX007_CHECKS": _CheckListBinding(
        private_attr="_EX007_CHECKS",
        public_attr="EX007_CHECKS",
    ),
}


def _resolve_check_list_binding(name: str) -> _CheckListBinding | None:
    normalized = name.lstrip("_")
    return _CHECK_LIST_BINDINGS.get(normalized)


def _mirror_package_aliases(
    module: ModuleType,
    binding: _CheckListBinding,
    assigned_name: str,
    value: Any,
) -> None:
    base_setattr = ModuleType.__setattr__
    for alias_name in (binding.private_attr, binding.public_attr):
        if alias_name == assigned_name:
            continue
        base_setattr(module, alias_name, value)


class _ChecksModule(ModuleType):
    def __setattr__(self, name: str, value: Any) -> None:
        ModuleType.__setattr__(self, name, value)
        binding = _resolve_check_list_binding(name)
        if binding is None:
            return
        _mirror_package_aliases(self, binding, name, value)


ResultT = TypeVar("ResultT", Ex002CheckResult, Ex006CheckResult, ExerciseCheckResult)


def _run_checks(
    checks: list[Any],
    result_type: type[ResultT],
) -> list[ResultT]:
    results: list[ResultT] = []
    for check in checks:
        try:
            issues = check.check()
        except NotebookGradingError as exc:
            issues = [str(exc)]
        results.append(
            result_type(
                exercise_no=check.exercise_no,
                title=check.title,
                passed=len(issues) == 0,
                issues=issues,
            )
        )
    return results


def _summary(results: list[ExerciseCheckResult | Ex002CheckResult | Ex006CheckResult]) -> list[str]:
    return [issue for result in results for issue in result.issues]


def check_ex002_summary() -> list[str]:
    """Run summary checks for ex002."""

    return _summary(run_ex002_checks())


def run_ex002_checks() -> list[Ex002CheckResult]:
    """Run detailed checks for ex002."""

    return _run_checks(_load_ex002_checks(), Ex002CheckResult)


def check_ex003() -> list[str]:
    """Run checks for ex003."""

    return _summary(run_ex003_checks())


def run_ex003_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex003."""

    return _run_checks(EX003_CHECKS, ExerciseCheckResult)


def check_ex004() -> list[str]:
    """Run checks for ex004."""

    return _summary(run_ex004_checks())


def run_ex004_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex004."""

    return _run_checks(EX004_CHECKS, ExerciseCheckResult)


def check_ex005() -> list[str]:
    """Run checks for ex005."""

    return _summary(run_ex005_checks())


def run_ex005_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex005."""

    return _run_checks(EX005_CHECKS, ExerciseCheckResult)


def check_ex006() -> list[str]:
    """Run checks for ex006."""

    return _summary(run_ex006_checks())


def run_ex006_checks() -> list[Ex006CheckResult]:
    """Run detailed checks for ex006."""

    return _run_checks(EX006_CHECKS, Ex006CheckResult)


def check_ex007() -> list[str]:
    """Run checks for ex007."""

    return _summary(run_ex007_checks())


def run_ex007_checks() -> list[ExerciseCheckResult]:
    """Run detailed checks for ex007."""

    return _run_checks(EX007_CHECKS, ExerciseCheckResult)


module = sys.modules[__name__]
if not isinstance(module, _ChecksModule):
    module.__class__ = _ChecksModule
