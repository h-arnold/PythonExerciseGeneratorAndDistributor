"""Stage 2 RED tests: runtimes and devcontainers move to Python 3.14.

Per ACTION_PLAN Stage 2 / SPEC acceptance criterion 2, every grading-runtime
pin must resolve Python 3.14 to match the Classroom 50 default grading
runtime. These tests assert the target state and therefore FAILED against the
previous 3.11/3.12 configuration (RED). No implementation, configuration, or
documentation file is changed by this module.

Scope note: 3.14 dependency compatibility is confirmed, so both
``pyproject.toml`` files now set the ``requires-python`` floor
unconditionally to ``>=3.14``. This test asserts the floor resolves the
3.14 grading runtime; it fails if the specifier ever excludes 3.14 (for
example an upper bound below 3.14 or a floor raised above it).
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from packaging.specifiers import SpecifierSet

EXPECTED_PYTHON_TAG = "3.14"
EXPECTED_DEVCONTAINER_IMAGE = f"mcr.microsoft.com/devcontainers/python:{EXPECTED_PYTHON_TAG}"

DEVCONTAINER_PATHS = (
    Path(".devcontainer/devcontainer.json"),
    Path("template_repo_files/.devcontainer/devcontainer.json"),
)

PYPROJECT_PATHS = (
    Path("pyproject.toml"),
    Path("template_repo_files/pyproject.toml"),
)


@dataclass(frozen=True)
class _DocPinExpectation:
    """Required and forbidden version-pin patterns for one Stage 2 doc surface."""

    path: Path
    required: tuple[str, ...]
    forbidden: tuple[str, ...]


DOC_PIN_EXPECTATIONS = (
    _DocPinExpectation(
        # Targets only the stale container-image pin ("installs Python 3.11").
        # The outside-container "Python 3.14 or later" prereq is out of scope
        # for this pin surface and must not be flagged.
        path=Path("docs/developers/setup.md"),
        required=(r"installs Python 3\.14\b",),
        forbidden=(r"installs Python 3\.(11|12|13)\b",),
    ),
    _DocPinExpectation(
        path=Path("docs/developers/docker-devcontainer-setup.md"),
        required=(r"Python 3\.14\b",),
        forbidden=(r"Python 3\.11\b", r"devcontainers/python:3\.(11|12)\b"),
    ),
    _DocPinExpectation(
        path=Path("docs/teachers/pedagogy.md"),
        required=(r"Python 3\.14\b",),
        forbidden=(r"Python 3\.11\b",),
    ),
)

_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
_PYTHON_VERSION_KEY_RE = re.compile(r"^\s*python-version\s*:(.*)$", re.IGNORECASE | re.MULTILINE)
_PYTHON_VERSION_ITEM_RE = re.compile(r"""^\s*-\s*['"]?(\d+\.\d+)['"]?\s*(?:#.*)?$""")
_VERSION_TOKEN_RE = re.compile(r"(\d+\.\d+)")


def _strip_jsonc_comments(text: str) -> str:
    """Remove ``//`` and ``/* */`` comments outside string literals.

    devcontainer.json files are VS Code JSONC: the student template carries
    ``//`` comments (and ``https://`` URLs whose ``//`` must survive), so a
    plain ``json.loads`` fails on them. String spans are matched first and
    passed through untouched; comments are removed only from code spans.
    """
    parts: list[str] = []
    pos = 0
    for match in _STRING_RE.finditer(text):
        parts.append(_COMMENT_RE.sub("", text[pos : match.start()]))
        parts.append(match.group(0))
        pos = match.end()
    parts.append(_COMMENT_RE.sub("", text[pos:]))
    return "".join(parts)


def _load_devcontainer_config(path: Path) -> dict[str, Any]:
    """Parse a devcontainer.json file, tolerating VS Code JSONC comments."""
    raw = _strip_jsonc_comments(path.read_text(encoding="utf-8"))
    config: dict[str, Any] = json.loads(raw)
    return config


def _repo_file(repo_root: Path, relative: Path) -> Path:
    """Resolve a repo-relative path, failing fast when the pin surface is missing."""
    candidate = repo_root / relative
    assert candidate.is_file(), f"expected Python pin surface is missing: {relative}"
    return candidate


def _workflow_python_pins(content: str) -> list[str]:
    """Extract literal ``python-version`` pins from workflow text.

    Handles scalar (``3.14``, ``"3.14"``), inline-list
    (``[3.13, 3.14]``), and block-sequence values. A trailing ``#``
    comment on the key line is ignored; block items must be a bare
    version (plus an optional comment) so commented-out text cannot
    contribute pins. Dynamic ``${{ ... }}`` expressions carry no literal
    pin and contribute nothing.
    """
    pins: list[str] = []
    lines = content.splitlines()
    for index, line in enumerate(lines):
        key = _PYTHON_VERSION_KEY_RE.match(line)
        if key is None:
            continue
        value = key.group(1).split(" #", 1)[0]
        pins.extend(_VERSION_TOKEN_RE.findall(value))
        for following in lines[index + 1 :]:
            item = _PYTHON_VERSION_ITEM_RE.match(following)
            if item is None:
                break
            pins.append(item.group(1))
    return pins


@pytest.mark.parametrize("relative", DEVCONTAINER_PATHS, ids=[str(p) for p in DEVCONTAINER_PATHS])
def test_devcontainer_image_pins_python_314(repo_root: Path, relative: Path) -> None:
    """Each devcontainer image must pin the Python 3.14 grading runtime."""
    config = _load_devcontainer_config(_repo_file(repo_root, relative))
    assert config.get("image") == EXPECTED_DEVCONTAINER_IMAGE, (
        f"{relative} image is {config.get('image')!r}, expected {EXPECTED_DEVCONTAINER_IMAGE!r}"
    )


@pytest.mark.parametrize(
    "expectation",
    DOC_PIN_EXPECTATIONS,
    ids=[str(e.path) for e in DOC_PIN_EXPECTATIONS],
)
def test_runtime_docs_reference_python_314(
    repo_root: Path, expectation: _DocPinExpectation
) -> None:
    """Stage 2 docs must state the 3.14 runtime pin with no stale version pins.

    Required patterns are word-boundary anchored (``Python 3.14`` rather than
    a bare ``3.14`` substring) so incidental numeric text such as ``3.14159``
    in a code sample cannot satisfy them.
    """
    content = _repo_file(repo_root, expectation.path).read_text(encoding="utf-8")
    for pattern in expectation.required:
        assert re.search(pattern, content), (
            f"{expectation.path} does not state the Python {EXPECTED_PYTHON_TAG} "
            f"runtime pin ({pattern!r})"
        )
    for pattern in expectation.forbidden:
        assert not re.search(pattern, content), (
            f"{expectation.path} still carries a stale Python pin ({pattern!r})"
        )


@pytest.mark.parametrize("relative", PYPROJECT_PATHS, ids=[str(p) for p in PYPROJECT_PATHS])
def test_requires_python_permits_314_without_floor_assumption(
    repo_root: Path, relative: Path
) -> None:
    """``requires-python`` must resolve the 3.14 grading runtime.

    Both floors are unconditionally ``>=3.14`` now that Stage 2 GREEN has
    confirmed 3.14 dependency compatibility. This test fails only if the
    specifier excludes 3.14 (for example an upper bound below 3.14).
    """
    with _repo_file(repo_root, relative).open("rb") as handle:
        requires_python = str(tomllib.load(handle)["project"]["requires-python"])
    spec = SpecifierSet(requires_python)
    assert spec.contains(EXPECTED_PYTHON_TAG, prereleases=True), (
        f"{relative} requires-python={requires_python!r} excludes Python {EXPECTED_PYTHON_TAG}"
    )


def test_ci_workflows_pin_python_314_when_present(repo_root: Path) -> None:
    """Every literal CI ``python-version`` pin must be exactly 3.14.

    Scalar, inline-list (``[3.13, 3.14]``), and block-sequence values are
    each inspected pin by pin, so a stale entry (3.11, 3.12, or 3.13)
    fails even alongside a 3.14 entry. Dynamic ``${{ ... }}`` expressions
    carry no literal pin and are out of scope. Files without literal pins
    pass; absence of workflow files skips.
    """
    workflow_dir = repo_root / ".github" / "workflows"
    candidates = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
    if not candidates:
        pytest.skip("no CI workflow files present, so no Python pin surface to check")
    for workflow in candidates:
        content = workflow.read_text(encoding="utf-8")
        for pin in _workflow_python_pins(content):
            assert pin == EXPECTED_PYTHON_TAG, (
                f"{workflow.name} pins python-version {pin!r}, "
                f"expected exactly {EXPECTED_PYTHON_TAG!r}"
            )
