"""Transcription of the documented Classroom 50 native assignment-manifest rules.

``SPEC.md`` (section "Native assignment-manifest requirements") and
``WORKFLOW_SPEC.md`` (section "Assignment manifest validation") record the pinned
``assignments-v1.schema.json`` rules, the upstream ``username_from_repo``
repository-identity derivation, and the upstream ``MODE`` to ``ASSIGNMENT_TYPE``
normalisation.  This repository does not own those upstream files, so the
documented rules are transcribed here once and exercised by
``tests/test_classroom50_native_autograder.py``.

This module is a *transcription of documented rules*, not a production validator
and not a substitute for the pinned schema.

Stage 7 cross-check: ``ACTION_PLAN.md`` Stage 7 pins
``schemas/assignments-v1.schema.json`` and the upstream ``runner.py`` at commit
``43ec1444f87674cd3276e66eadb6439dc0c97668`` behind a SHA-256 manifest.  Until
that snapshot lands, every rule below must be re-checked against it, because
``SPEC.md`` requires the native contract fixture to avoid "a hand-written
substitute".
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeGuard

ASSIGNMENT_TYPES = ("individual", "group", "team")
TEAM_FORMATIONS = ("teacher", "student")
MIN_MAX_GROUP_SIZE = 2
MAX_MAX_GROUP_SIZE = 100
DEFAULT_MAX_GROUP_SIZE = 3
NATIVE_AUTOGRADER_NAME = "default"
AUTO_GRADING_MODE = "auto"
REQUIRED_MANIFEST_FIELDS = ("slug", "name")
OMITTED_FALSE_FLAGS = ("empty_repo", "no_autograder")
TEMPLATE_FIELDS = ("owner", "repo", "branch")
TEMPLATE_FIXTURE: dict[str, object] = {
    "owner": "classroom50-fixture",
    "repo": "native-starter-template",
    "branch": "main",
}

# Sentinel that removes a key from a generated assignment-manifest fixture.
ABSENT = object()

MAX_GROUP_SIZE_RANGE = f"{MIN_MAX_GROUP_SIZE}-{MAX_MAX_GROUP_SIZE}"


def is_manifest_object(value: object) -> TypeGuard[dict[str, object]]:
    """Return True when a manifest fragment is a JSON object."""
    return isinstance(value, dict)


def _is_int(value: object) -> TypeGuard[int]:
    """Return True when a manifest value is a real integer, not a boolean."""
    return isinstance(value, int) and not isinstance(value, bool)


def _non_empty_str(value: object) -> bool:
    """Return True when a manifest value is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def is_valid_template(template: object) -> bool:
    """Return True when ``template`` is an object with non-empty owner/repo/branch.

    A native bundle assignment needs the template because the student checkout
    must contain the canonical exercise metadata, notebooks, and visible tests
    that the bundle deliberately excludes.
    """
    if not is_manifest_object(template):
        return False
    return all(_non_empty_str(template.get(field)) for field in TEMPLATE_FIELDS)


def assignment_entry(mode: str) -> dict[str, Any]:
    """Return one valid native assignment-manifest fixture for a supported mode."""
    entry: dict[str, Any] = {
        "slug": "native-contract-assignment",
        "name": "Native contract assignment",
        "autograder": NATIVE_AUTOGRADER_NAME,
        "grading": {"mode": AUTO_GRADING_MODE},
        "mode": mode,
        "private": True,
        "template": dict(TEMPLATE_FIXTURE),
    }
    if mode in ("group", "team"):
        entry["max_group_size"] = DEFAULT_MAX_GROUP_SIZE
    if mode == "team":
        entry["team_formation"] = TEAM_FORMATIONS[0]
    return entry


def with_overrides(entry: Mapping[str, Any], **overrides: Any) -> dict[str, Any]:
    """Return a copy of ``entry`` with ``overrides`` applied; ``ABSENT`` removes a key."""
    mutated = dict(entry)
    for key, value in overrides.items():
        if value is ABSENT:
            mutated.pop(key, None)
        else:
            mutated[key] = value
    return mutated


def _required_field_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return problems for required ``slug``/``name`` values."""
    return [
        f"{field} must be a non-empty string"
        for field in REQUIRED_MANIFEST_FIELDS
        if not _non_empty_str(entry.get(field))
    ]


def _autograder_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return problems for the ``autograder`` short name."""
    if entry.get("autograder") == NATIVE_AUTOGRADER_NAME:
        return []
    return [f"autograder must be the string {NATIVE_AUTOGRADER_NAME!r}"]


def _grading_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return problems for the autograding block; an omitted mode means ``auto``."""
    if "grading" not in entry:
        return []
    grading = entry["grading"]
    if not is_manifest_object(grading):
        return ["grading must be an object when present"]
    if "mode" in grading and grading["mode"] != AUTO_GRADING_MODE:
        return [f"grading.mode must be {AUTO_GRADING_MODE!r} or omitted"]
    return []


def _flag_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return problems for the boolean flags that must be false or omitted."""
    problems: list[str] = []
    for flag in OMITTED_FALSE_FLAGS:
        if flag not in entry:
            continue
        value = entry[flag]
        if value is True:
            problems.append(f"{flag} must be false or omitted")
        elif not isinstance(value, bool):
            problems.append(f"{flag} must be a boolean when present")
    return problems


def _group_size_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return ``max_group_size`` problems for the entry's mode."""
    mode = entry["mode"]
    if mode not in ("group", "team"):
        return [f"{mode} must omit max_group_size"] if "max_group_size" in entry else []
    max_group_size = entry.get("max_group_size")
    if not _is_int(max_group_size):
        return [f"{mode} requires an integer max_group_size in {MAX_GROUP_SIZE_RANGE}"]
    if not MIN_MAX_GROUP_SIZE <= max_group_size <= MAX_MAX_GROUP_SIZE:
        return [f"max_group_size must be within {MAX_GROUP_SIZE_RANGE}"]
    return []


def _team_formation_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return ``team_formation`` problems for the entry's mode."""
    mode = entry["mode"]
    if mode == "team":
        if entry.get("team_formation") not in TEAM_FORMATIONS:
            return [f"team_formation must be one of {TEAM_FORMATIONS}"]
        return []
    return [f"{mode} must omit team_formation"] if "team_formation" in entry else []


def _mode_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return the supported-mode and conditional field problems."""
    mode = entry.get("mode")
    if mode not in ASSIGNMENT_TYPES:
        return [f"mode must be one of {ASSIGNMENT_TYPES}, got {mode!r}"]
    return [*_group_size_problems(entry), *_team_formation_problems(entry)]


def _init_shim_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return the ``init_shim`` exclusivity and flag-exclusion problems."""
    if entry.get("init_shim") is not True:
        return []
    problems: list[str] = []
    if "template" in entry:
        problems.append("init_shim and template are mutually exclusive")
    problems.extend(
        f"init_shim excludes {flag}" for flag in OMITTED_FALSE_FLAGS if entry.get(flag) is True
    )
    return problems


def assignment_schema_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return every violation of the transcribed pinned ``assignments-v1`` rules.

    An empty list means the entry satisfies the rules that ``SPEC.md`` and
    ``WORKFLOW_SPEC.md`` document for a native bundle assignment.  Problem
    strings are stable so tests can assert the exact full list.
    """
    problems = [
        *_required_field_problems(entry),
        *_autograder_problems(entry),
        *_grading_problems(entry),
        *_flag_problems(entry),
    ]
    if "tests" in entry:
        problems.append("tests must be absent")
    problems.extend(_mode_problems(entry))
    problems.extend(_init_shim_problems(entry))
    return problems


def native_deployment_problems(entry: Mapping[str, Any]) -> list[str]:
    """Return schema violations plus the native-deployment-only restrictions.

    A template-less ``init_shim`` entry is schema-valid but is rejected for this
    native bundle deployment because it creates no starter exercise surface.
    """
    problems = list(assignment_schema_problems(entry))
    if entry.get("init_shim") is True:
        problems.append("init_shim is unsupported for the native bundle deployment")
    if not is_valid_template(entry.get("template")):
        problems.append(
            "native deployment requires a template with non-empty owner, repo, and branch"
        )
    return problems


def username_from_repo(repository: str, classroom: str, assignment: str, actor: str) -> str:
    """Transcribe the upstream ``username_from_repo`` repository-identity derivation.

    ``SPEC.md`` (section "Invocation and environment contract") records that the
    expected ``<classroom>-<assignment>-`` prefix is stripped case-insensitively,
    the remaining repository tail is used (including ``group-<n>`` group/team
    tails), and the GitHub actor is the fallback.  The tail is used verbatim; no
    case folding or trimming is transcribed because the contract does not
    specify any.
    """
    prefix = f"{classroom}-{assignment}-"
    if repository.lower().startswith(prefix.lower()):
        tail = repository[len(prefix) :]
        if tail:
            return tail
    return actor


def assignment_type_from_mode(mode: str) -> str:
    """Transcribe the upstream ``MODE`` to ``ASSIGNMENT_TYPE`` normalisation.

    ``SPEC.md`` (section "Invocation and environment contract") states only that
    ``ASSIGNMENT_TYPE`` is normalised from the runner's ``MODE`` value, and the
    agreed decisions accept exactly ``individual``, ``group``, and ``team``.  Only
    that support set is transcribed: the three supported modes map onto
    themselves and any other value is rejected.  Whitespace trimming and case
    folding are deliberately *not* transcribed because the contract does not
    specify them.
    """
    if mode not in ASSIGNMENT_TYPES:
        raise ValueError(f"Unsupported MODE value: {mode!r}")
    return mode
