"""Check implementations for each notebook."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any, Final, NamedTuple

from tests.notebooks.ex001_sanity import checker as ex001
from tests.notebooks.ex001_sanity.checker import check_ex001
from tests.notebooks.ex002_sequence_modify_basics import checker as ex002
from tests.notebooks.ex002_sequence_modify_basics.checker import (
    check_ex002_summary,
    run_ex002_checks,
)
from tests.notebooks.ex003_sequence_modify_variables import checker as ex003
from tests.notebooks.ex003_sequence_modify_variables.checker import (
    EX003_CHECKS,
    check_ex003,
    run_ex003_checks,
)
from tests.notebooks.ex004_sequence_debug_syntax import checker as ex004
from tests.notebooks.ex004_sequence_debug_syntax.checker import (
    EX004_CHECKS,
    check_ex004,
    run_ex004_checks,
)
from tests.notebooks.ex005_sequence_debug_logic import checker as ex005
from tests.notebooks.ex005_sequence_debug_logic.checker import (
    EX005_CHECKS,
    check_ex005,
    run_ex005_checks,
)
from tests.notebooks.ex006_sequence_modify_casting import checker as ex006
from tests.notebooks.ex006_sequence_modify_casting.checker import (
    EX006_CHECKS,
    check_ex006,
    run_ex006_checks,
)
from tests.notebooks.ex007_data_types_debug_casting import checker as ex007
from tests.notebooks.ex007_data_types_debug_casting.checker import (
    EX007_CHECKS,
    check_ex007,
    run_ex007_checks,
)

from .base import Ex006CheckDefinition, ExerciseCheckDefinition

_EX003_CHECKS = EX003_CHECKS
_EX004_CHECKS = EX004_CHECKS
_EX005_CHECKS = EX005_CHECKS
_EX006_CHECKS = EX006_CHECKS
_EX007_CHECKS = EX007_CHECKS
_MODULE_ALIASES = (ex001, ex002, ex003, ex004, ex005, ex006, ex007)

__all__ = [
    "EX003_CHECKS",
    "EX004_CHECKS",
    "EX005_CHECKS",
    "EX006_CHECKS",
    "EX007_CHECKS",
    "Ex006CheckDefinition",
    "ExerciseCheckDefinition",
    "check_ex001",
    "check_ex002_summary",
    "check_ex003",
    "check_ex004",
    "check_ex005",
    "check_ex006",
    "check_ex007",
    "ex001",
    "ex002",
    "ex003",
    "ex004",
    "ex005",
    "ex006",
    "ex007",
    "run_ex002_checks",
    "run_ex003_checks",
    "run_ex004_checks",
    "run_ex005_checks",
    "run_ex006_checks",
    "run_ex007_checks",
]


class _CheckListBinding(NamedTuple):
    module_name: str
    private_attr: str
    public_attr: str


_CHECK_LIST_BINDINGS: Final[dict[str, _CheckListBinding]] = {
    "EX003_CHECKS": _CheckListBinding(
        module_name="tests.notebooks.ex003_sequence_modify_variables.checker",
        private_attr="_EX003_CHECKS",
        public_attr="EX003_CHECKS",
    ),
    "EX004_CHECKS": _CheckListBinding(
        module_name="tests.notebooks.ex004_sequence_debug_syntax.checker",
        private_attr="_EX004_CHECKS",
        public_attr="EX004_CHECKS",
    ),
    "EX005_CHECKS": _CheckListBinding(
        module_name="tests.notebooks.ex005_sequence_debug_logic.checker",
        private_attr="_EX005_CHECKS",
        public_attr="EX005_CHECKS",
    ),
    "EX006_CHECKS": _CheckListBinding(
        module_name="tests.notebooks.ex006_sequence_modify_casting.checker",
        private_attr="_EX006_CHECKS",
        public_attr="EX006_CHECKS",
    ),
    "EX007_CHECKS": _CheckListBinding(
        module_name="tests.notebooks.ex007_data_types_debug_casting.checker",
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


def _propagate_to_submodule(binding: _CheckListBinding, value: Any) -> None:
    module = sys.modules.get(binding.module_name)
    if module is None:
        return
    setattr(module, binding.private_attr, value)
    setattr(module, binding.public_attr, value)


class _ChecksModule(ModuleType):
    def __setattr__(self, name: str, value: Any) -> None:
        ModuleType.__setattr__(self, name, value)
        binding = _resolve_check_list_binding(name)
        if binding is None:
            return
        _mirror_package_aliases(self, binding, name, value)
        _propagate_to_submodule(binding, value)


module = sys.modules[__name__]
if not isinstance(module, _ChecksModule):
    module.__class__ = _ChecksModule
