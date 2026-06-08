"""Exercise scaffold classes for generating exercises by type."""

from scripts.exercise_scaffolder.base import ExerciseScaffold
from scripts.exercise_scaffolder.debug import DebugScaffold
from scripts.exercise_scaffolder.gaps import GapsScaffold
from scripts.exercise_scaffolder.make import MakeScaffold
from scripts.exercise_scaffolder.modify import ModifyScaffold

__all__ = [
    "DebugScaffold",
    "ExerciseScaffold",
    "GapsScaffold",
    "MakeScaffold",
    "ModifyScaffold",
]
