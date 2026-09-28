"""Lock-derived requirements data for the Stage 3 Classroom 50 native contract.

``ACTION_PLAN.md`` Stage 3 installs a committed, lock-parity-checked requirements
file into a fresh bundle-local target before the grader may import pytest.  The
expected pins are therefore *derived* from ``uv.lock`` here rather than restated,
so a lock change shows up as a test failure instead of a second copy of the
expected pins, and the active-platform subset is a real marker evaluation.

This module owns the committed source paths the bundle contract is built from -
the lockfile, the native requirements source, and the repository's broad root
``pytest.ini`` that a bundle must never reuse - plus the parsing of a
requirements file into pins and platform markers.  The seam harness in
``tests/_classroom50_bootstrap.py`` consumes the rendered fixture; the AST
helpers live in ``tests/_classroom50_source_scan.py``.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from packaging.markers import Marker
from packaging.requirements import Requirement

from tests._classroom50_test_helpers import REPO_ROOT

UV_LOCK: Final[Path] = REPO_ROOT / "uv.lock"
REQUIREMENTS_SOURCE: Final[Path] = REPO_ROOT / "scripts" / "classroom50_requirements.txt"
REPOSITORY_PYTEST_INI: Final[Path] = REPO_ROOT / "pytest.ini"

# The marker the lockfile uses for the Windows-only dependency of pytest, and the
# normalised spelling a committed requirements line has to keep.
WINDOWS_PLATFORM_MARKER: Final[str] = 'sys_platform == "win32"'

# Roots of the native requirement closure: pytest plus the runtime package that
# ``exercise_runtime_support.exercise_framework.reporting`` imports directly.
LOCK_CLOSURE_ROOT: Final[str] = "pytest"
DIRECT_NATIVE_REQUIREMENTS: Final[tuple[str, ...]] = ("tabulate",)


def committed_requirements_bytes() -> bytes:
    """Return the committed lock-derived requirements source, or fail naming its path."""
    assert REQUIREMENTS_SOURCE.is_file(), (
        f"{REQUIREMENTS_SOURCE} is not committed yet; Stage 3 adds the "
        "lock-parity-checked native requirements source."
    )
    return REQUIREMENTS_SOURCE.read_bytes()


def _uv_lock_packages() -> dict[str, Mapping[str, Any]]:
    """Return every package recorded in ``uv.lock``, keyed by its canonical name."""
    with UV_LOCK.open("rb") as handle:
        lock = tomllib.load(handle)
    return {package["name"]: package for package in lock["package"]}


def _lock_closure(evaluate_markers: bool) -> list[str]:
    """Return the native requirement closure in lock order, optionally filtered."""
    packages = _uv_lock_packages()
    ordered: list[str] = []
    queue: list[str] = [LOCK_CLOSURE_ROOT, *DIRECT_NATIVE_REQUIREMENTS]
    while queue:
        name = queue.pop(0)
        if name in ordered:
            continue
        ordered.append(name)
        for dependency in packages[name].get("dependencies", []):
            marker = dependency.get("marker")
            if evaluate_markers and marker is not None and not Marker(marker).evaluate():
                continue
            queue.append(dependency["name"])
    return ordered


def locked_closure_pins() -> dict[str, str]:
    """Return every locked native pin for every platform, markers ignored."""
    packages = _uv_lock_packages()
    return {name: str(packages[name]["version"]) for name in _lock_closure(False)}


def locked_markers() -> dict[str, str]:
    """Return the normalised lockfile marker of each marked closure member."""
    packages = _uv_lock_packages()
    markers: dict[str, str] = {}
    for name in _lock_closure(False):
        for dependency in packages[name].get("dependencies", []):
            marker = dependency.get("marker")
            if marker is not None:
                markers[dependency["name"]] = str(Marker(str(marker)))
    return markers


def locked_active_pins() -> dict[str, str]:
    """Return the locked native pins required on the active platform."""
    pins = locked_closure_pins()
    markers = locked_markers()
    return {
        name: version
        for name, version in pins.items()
        if name not in markers or Marker(markers[name]).evaluate()
    }


def windows_active() -> bool:
    """Return True when the active platform marker selects the Windows-only pins."""
    return Marker(WINDOWS_PLATFORM_MARKER).evaluate()


def _parsed_requirements(requirements_text: str) -> dict[str, Requirement]:
    """Return every requirement in ``requirements_text`` keyed by its name.

    Blank lines and comments are ignored.  A non-``==`` requirement fails fast:
    the native requirements source is a set of exact pins, so a range, an extras
    request, an editable reference, or a URL is a contract violation rather than
    something to tolerate.
    """
    parsed: dict[str, Requirement] = {}
    for line in requirements_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        requirement = Requirement(stripped)
        specifiers = list(requirement.specifier)
        assert len(specifiers) == 1 and specifiers[0].operator == "==", (
            f"{stripped!r} must be one exact 'name==version' pin; the native "
            "requirements source is not a range, extra, or URL list."
        )
        assert requirement.url is None and not requirement.extras, (
            f"{stripped!r} must be a plain pinned requirement."
        )
        assert requirement.name not in parsed, f"{requirement.name!r} is pinned twice."
        parsed[requirement.name] = requirement
    return parsed


def _pinned_version(requirement: Requirement) -> str:
    """Return the single pinned version of an exact-pin requirement."""
    return str(next(iter(requirement.specifier)).version)


def requirement_pins(requirements_text: str) -> dict[str, str]:
    """Return every pinned version in ``requirements_text``, ignoring markers."""
    return {
        name: _pinned_version(item)
        for name, item in _parsed_requirements(requirements_text).items()
    }


def requirement_markers(requirements_text: str) -> dict[str, str]:
    """Return the normalised marker text of each marked requirement."""
    return {
        name: str(Marker(str(item.marker)))
        for name, item in _parsed_requirements(requirements_text).items()
        if item.marker is not None
    }


def active_platform_pins(requirements_text: str) -> dict[str, str]:
    """Return the pins whose environment marker holds for the active platform."""
    return {
        name: _pinned_version(item)
        for name, item in _parsed_requirements(requirements_text).items()
        if item.marker is None or item.marker.evaluate()
    }


def lock_derived_requirements() -> str:
    """Render a requirements source from the locked native closure.

    A staged native bundle needs a file that behaves like the committed one -
    including the lockfile's own platform markers - without the bootstrap tests
    depending on the committed source existing yet.
    """
    packages = _uv_lock_packages()
    markers = locked_markers()
    return "".join(
        f"{name}=={packages[name]['version']}"
        + (f"; {markers[name]}\n" if name in markers else "\n")
        for name in _lock_closure(False)
    )
