"""Check implementations for each notebook."""

from __future__ import annotations

from .base import Ex006CheckDefinition, ExerciseCheckDefinition
from .ex001 import check_ex001
from .ex002 import check_ex002_summary, run_ex002_checks
from .ex003 import _EX003_CHECKS, check_ex003, run_ex003_checks
from .ex004 import _EX004_CHECKS, check_ex004, run_ex004_checks
from .ex005 import _EX005_CHECKS, check_ex005, run_ex005_checks
from .ex006 import _EX006_CHECKS, check_ex006, run_ex006_checks
from .ex007 import _EX007_CHECKS, check_ex007, run_ex007_checks

__all__ = [
    "_EX003_CHECKS",
    "_EX004_CHECKS",
    "_EX005_CHECKS",
    "_EX006_CHECKS",
    "_EX007_CHECKS",
    "Ex006CheckDefinition",
    "ExerciseCheckDefinition",
    "check_ex001",
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
