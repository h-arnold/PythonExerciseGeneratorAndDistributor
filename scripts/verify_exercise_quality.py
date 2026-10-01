#!/usr/bin/env python3
"""Lightweight verifier for canonical exercises identified by ``exercise_key``.

This script supports the Exercise Reviewer agent by performing fast,
objective checks against ``exercises/<construct>/<exercise_key>/``:
- Notebook structure: metadata.language, code-vs-tag consistency
- Presence of expected tags (exerciseN, explanationN)
- Basic concept progression scanning (heuristic keyword checks over executable
  code only; comment and string literal text is prose, and casting is a
  documented prerequisite of the first two constructs)
- Presence of required canonical exercise files under exercises/
- Construct teaching order updated (exercises/<construct>/OrderOfTeaching.md)
- Student checker support module, expectations module, variant overrides,
  and runtime self-check (Gates F-I)

The ``--skip-empty-checks`` flag suppresses the Gate F error when the
``CHECKS`` list in ``student_checker_support.py`` is empty, allowing the
verifier to be used during Phase 1 (notebook authoring) before checker
definitions are written.

The public CLI accepts the canonical ``exercise_key`` only, or ``--all`` to run
the same gate set across every discovered exercise and aggregate the result. It
is not a replacement for reading the exercise prompts.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict, TypeGuard, cast

from exercise_metadata import load_exercise_metadata, resolve_exercise_dir

CONSTRUCT_ORDER: list[str] = [
    "sequence",
    "selection",
    "iteration",
    "data_types",
    "lists",
    "dictionaries",
    "functions",
    "file_handling",
    "exceptions",
    "libraries",
    "oop",
]

EXERCISE_TYPES = frozenset({"debug", "modify", "make", "gaps"})

# Token kinds that carry executable code. Every other kind is prose and is blanked
# out before the progression patterns run: comments, string literals, and the
# literal chunks of an f-string or t-string. The layout kinds (NEWLINE, NL,
# INDENT, DEDENT, ENDMARKER) are kept because the patterns match across lines.
# Anything this set does not name is treated as prose, so a token kind introduced
# by a future Python release cannot invent new warnings.
_EXECUTABLE_TOKEN_TYPES = frozenset(
    {
        tokenize.NAME,
        tokenize.NUMBER,
        tokenize.OP,
        tokenize.NEWLINE,
        tokenize.NL,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
    }
)

# A string literal the tokenizer cannot close is the one failure that leaves prose
# in the source: it stops inside the literal, so the rest of that literal emits no
# token to blank and runs on to the end of the cell. An ordinary, byte, or
# triple-quoted string emits no token at all before failing, so the unread text
# itself opens the literal; the optional prefix and the three quote styles cover
# every such literal the tokenizer can stop on. The prefix is only the letters a
# string prefix is made of (`r`, `u`, `b`, `f`, `t`, in either case) and at most
# the two letters the longest valid prefix has, so an unrelated run of letters —
# a mistyped `s"` — reads as a name and cannot mask the code after it.
_STRING_OPENING_RE = re.compile(r"[ \t]*[rRuUbBfFtT]{0,2}(?:\"\"\"|'''|\"|')")

# Since PEP 701 (Python 3.12) an f-string or t-string arrives as several tokens:
# the opening token, then its literal text and replacement fields in turn, then
# the closing token. An unfinished one therefore leaves its opening token behind,
# which is what tells the tokenizer stopped in literal text. The repository
# runtime pins Python 3.14, so a constant this runtime does not have fails at
# import. They are read out of the module namespace rather than as attributes
# because typeshed only declares them from Python 3.12 while this repository
# type-checks against 3.11.
_LITERAL_OPEN_TOKEN_TYPES = frozenset(
    vars(tokenize)[name] for name in ("FSTRING_START", "TSTRING_START")
)
_LITERAL_CLOSE_TOKEN_TYPES = frozenset(
    vars(tokenize)[name] for name in ("FSTRING_END", "TSTRING_END")
)

# int()/float()/str() casting is a documented prerequisite for the first two
# constructs rather than a progression violation:
#
# - exercises/sequence/OrderOfTeaching.md teaches casting in ex006
#   (`ex006_sequence_modify_casting`) and ex007 (`ex007_sequence_debug_casting`),
#   part-way through the sequence strand.
# - The selection strand starts at `ex001_selection_modify_basics`, which
#   compares values read from `input()`, so it needs those casts already taught.
#
# Every other later construct (iteration, exceptions, and the rest) is still
# detected for these constructs.
_CASTING_PREREQUISITE_CONSTRUCTS = frozenset({"sequence", "selection"})


@dataclass(frozen=True)
class Finding:
    severity: str  # "ERROR" or "WARN"
    message: str
    path: Path | None = None


class _ExerciseMetadataError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        super().__init__(message)
        self.path = path


@dataclass(frozen=True)
class _VerifyOptions:
    """Per-invocation verifier flags that are not derived from exercise metadata.

    Attributes:
        construct: Overrides the construct inferred from ``exercise.json``;
            ``None`` keeps the inferred value.
        exercise_type: Overrides the exercise type inferred from
            ``exercise.json``; ``None`` keeps the inferred value.
        skip_empty_checks: Gate F flag that suppresses the empty-CHECKS error.
    """

    construct: str | None = None
    exercise_type: str | None = None
    skip_empty_checks: bool = False


NotebookCellSource = str | list[str]


class NotebookCellMetadata(TypedDict, total=False):
    language: str
    tags: NotebookCellSource


class NotebookCell(TypedDict, total=False):
    cell_type: str
    metadata: NotebookCellMetadata
    source: NotebookCellSource


class NotebookDocument(TypedDict, total=False):
    cells: list[NotebookCell]


def _is_notebook_cell_source(value: object) -> TypeGuard[NotebookCellSource]:
    if isinstance(value, str):
        return True
    if not isinstance(value, list):
        return False
    value_list: list[object] = cast(list[object], value)
    return all(isinstance(item, str) for item in value_list)


def _is_notebook_cell_metadata(value: object) -> TypeGuard[NotebookCellMetadata]:
    if not isinstance(value, dict):
        return False
    metadata = cast(dict[str, Any], value)
    language = metadata.get("language")
    if language is not None and not isinstance(language, str):
        return False
    tags = metadata.get("tags")
    if tags is None:
        return True
    if isinstance(tags, str):
        return True
    if isinstance(tags, list):
        tags_list: list[object] = cast(list[object], tags)
        return all(isinstance(tag, str) for tag in tags_list)
    return False


def _is_notebook_cell(value: object) -> TypeGuard[NotebookCell]:
    if not isinstance(value, dict):
        return False
    cell = cast(dict[str, Any], value)
    cell_type = cell.get("cell_type")
    if cell_type is not None and not isinstance(cell_type, str):
        return False
    metadata = cell.get("metadata")
    if metadata is not None and not _is_notebook_cell_metadata(metadata):
        return False
    source = cell.get("source")
    if source is None:
        return True
    return _is_notebook_cell_source(source)


def _is_notebook_cells(value: object | None) -> TypeGuard[list[NotebookCell]]:
    if not isinstance(value, list):
        return False
    typed_cells: list[object] = cast(list[object], value)
    return all(_is_notebook_cell(item) for item in typed_cells)


def _is_notebook_document(value: object) -> TypeGuard[NotebookDocument]:
    if not isinstance(value, dict):
        return False
    mapping = cast(dict[str, Any], value)
    return _is_notebook_cells(mapping.get("cells"))


def _load_notebook(path: Path) -> NotebookDocument:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Notebook not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in notebook: {path}: {exc}") from exc

    if not _is_notebook_document(raw):
        raise SystemExit(f"Notebook {path} is missing a top-level 'cells' list.")
    return raw


def _cell_tags(cell: NotebookCell) -> set[str]:
    metadata: NotebookCellMetadata | None = cell.get("metadata")
    if metadata is None or "tags" not in metadata:
        return set()

    raw_tags = metadata["tags"]
    if isinstance(raw_tags, list):
        tags: set[str] = set()
        raw_tags_list: list[object] = cast(list[object], raw_tags)
        for tag in raw_tags_list:
            if isinstance(tag, str):
                tags.add(tag)
        return tags
    return {raw_tags}


def _cell_source_text(cell: NotebookCell) -> str:
    if "source" not in cell:
        return ""
    source = cell["source"]
    if isinstance(source, list):
        return "\n".join(source)
    return source


_EXERCISE_TAG_RE = re.compile(r"^exercise(?P<n>\d+)$")
_EXPLANATION_TAG_RE = re.compile(r"^explanation(?P<n>\d+)$")
# Heuristic detection of input() calls — used to cross-check expectations.py
# classification (static vs interactive).  May produce false positives for
# input in comments/strings, which is acceptable for a lint-style verifier.
_INPUT_CALL_RE = re.compile(r"\binput\s*\(")
# Canonical exercise directory names, e.g. ex004_sequence_debug_syntax.  Sweep
# discovery matches on this shape rather than on the presence of exercise.json
# so that an exercise with missing or invalid metadata is still verified, while
# sibling directories that are not exercises (e.g. additional-resources) are
# left alone.
_EXERCISE_DIR_RE = re.compile(r"^ex\d+_\w+$")
# Module-level expectation dicts are named EX<N>_<CONVENTION>, where the
# convention says what the dict declares for each exercise number.
_EXPECTATION_NAME_RE = re.compile(r"^EX\d+_(?P<convention>[A-Z0-9_]+)$")
# The expectation-dict conventions the shipped exercises use.  An exercise may
# split its expectations across several dicts — static, interactive, or one per
# output shape — so coverage is the union of the part keys of every recognised
# dict rather than the keys of a single ``EX<N>_EXPECTED_OUTPUTS`` dict.
#
# ``_STATIC_EXPECTATION_CONVENTIONS`` declare what a part prints without reading
# input.  ``_INTERACTIVE_EXPECTATION_CONVENTIONS`` declare a runnable input case,
# or the prompts/inputs/post-input message such a case is driven with, for a
# part whose code calls ``input()``.  Dicts in neither set — supplementary
# ``EX<N>_EDGE_CASES`` or ``EX<N>_ORIGINAL_PROMPTS`` data, and reference aliases
# computed from an input-case dict — count as neither coverage nor a runnable
# input case.
_STATIC_EXPECTATION_CONVENTIONS = frozenset(
    {
        "EXPECTED_OUTPUTS",
        "EXPECTED_STATIC_OUTPUT",
        "EXPECTED_STATIC_OUTPUTS",
        "EXPECTED_SINGLE_LINE",
        "EXPECTED_MULTI_LINE",
        "EXPECTED_NUMERIC",
        "EXPECTED_PRINT_CALLS",
    }
)
_INTERACTIVE_EXPECTATION_CONVENTIONS = frozenset(
    {
        "INPUT_CASES",
        "INPUT_EXPECTATIONS",
        "INTERACTIVE_CASES",
        "EXPECTED_PROMPTS",
        "PROMPT_STRINGS",
        "INPUT_PROMPTS",
        "EXERCISE_INPUTS",
        "FORMAT_VALIDATION",
    }
)
# The one field a quick-reference dict may copy out of an input case to count as a
# mirror of it.  See _mirrors_input_cases.
_EXPECTED_OUTPUT_KEY = "expected_output"


def _load_canonical_metadata(ex_dir: Path) -> dict[str, Any]:
    metadata_path = ex_dir / "exercise.json"
    try:
        metadata = load_exercise_metadata(ex_dir)
    except FileNotFoundError as exc:
        raise _ExerciseMetadataError(metadata_path, str(exc)) from exc
    except ValueError as exc:
        raise _ExerciseMetadataError(metadata_path, str(exc)) from exc

    return dict(metadata)


def _load_construct_and_type(ex_dir: Path) -> tuple[str, str]:
    metadata = _load_canonical_metadata(ex_dir)
    metadata_path = ex_dir / "exercise.json"

    construct = metadata.get("construct")
    if not isinstance(construct, str) or construct not in CONSTRUCT_ORDER:
        raise _ExerciseMetadataError(
            metadata_path,
            "Canonical exercise metadata must define a valid construct",
        )

    exercise_type = metadata.get("exercise_type")
    if not isinstance(exercise_type, str) or exercise_type not in EXERCISE_TYPES:
        raise _ExerciseMetadataError(
            metadata_path,
            "Canonical exercise metadata must define a valid exercise_type",
        )

    exercise_key = metadata.get("exercise_key")
    if not isinstance(exercise_key, str):
        raise _ExerciseMetadataError(
            metadata_path,
            "Canonical exercise metadata must define exercise_key as a string",
        )
    if exercise_key != ex_dir.name:
        raise _ExerciseMetadataError(
            metadata_path,
            "Canonical exercise metadata exercise_key "
            f"{exercise_key!r} must match directory name {ex_dir.name!r}",
        )

    return construct, exercise_type


def _check_canonical_structure(ex_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    required = [
        ex_dir / "README.md",
        ex_dir / "notebooks" / "student.ipynb",
        ex_dir / "notebooks" / "solution.ipynb",
        ex_dir / "tests" / f"test_{ex_dir.name}.py",
    ]
    for required_path in required:
        if not required_path.exists():
            findings.append(
                Finding(
                    "ERROR",
                    f"Missing canonical file: {required_path.relative_to(ex_dir)}",
                    path=required_path,
                )
            )

    return findings


def _check_order_of_teaching(
    ex_dir: Path,
    *,
    construct: str | None,
    repo_root: Path,
    notebook_name: str,
) -> list[Finding]:
    findings: list[Finding] = []

    if construct is None:
        findings.append(
            Finding(
                "WARN",
                "Could not infer construct for OrderOfTeaching.md check",
                path=ex_dir,
            )
        )
        return findings

    order_path = repo_root / "exercises" / construct / "OrderOfTeaching.md"
    if not order_path.exists():
        findings.append(
            Finding(
                "ERROR",
                f"Missing construct teaching order file: exercises/{construct}/OrderOfTeaching.md",
                path=order_path,
            )
        )
        return findings

    text = order_path.read_text(encoding="utf-8")
    slug = ex_dir.name
    # Accept the current legacy flattened notebook reference plus canonical exercise-local
    # notebook references while construct teaching-order files are still mid-migration.
    notebook_refs = {
        f"notebooks/{slug}.ipynb",
        f"{slug}/notebooks/{notebook_name}",
        f"{construct}/{slug}/notebooks/{notebook_name}",
    }

    if slug not in text and not any(notebook_ref in text for notebook_ref in notebook_refs):
        findings.append(
            Finding(
                "ERROR",
                "OrderOfTeaching.md does not mention this exercise (add the exercise folder name or notebook path)",
                path=order_path,
            )
        )

    return findings


def _check_cell_language(cell_index: int, cell: NotebookCell, nb_path: Path) -> list[Finding]:
    metadata: NotebookCellMetadata | None = cell.get("metadata")
    lang: str | None = None
    if metadata is not None and "language" in metadata:
        lang = metadata["language"]
    if lang in {"python", "markdown"}:
        return []
    return [
        Finding(
            "ERROR",
            f"Cell {cell_index} missing/invalid metadata.language (expected 'python' or 'markdown')",
            path=nb_path,
        )
    ]


def _collect_tag_findings(
    *,
    cell_type: str | None,
    tags: set[str],
    nb_path: Path,
) -> tuple[set[str], set[str], list[Finding]]:
    exercise_tags: set[str] = set()
    explanation_tags: set[str] = set()
    findings: list[Finding] = []

    for tag in tags:
        if _EXERCISE_TAG_RE.match(tag):
            exercise_tags.add(tag)
            if cell_type != "code":
                findings.append(
                    Finding(
                        "ERROR",
                        f"Tag {tag} must be on a code cell (found on {cell_type!r})",
                        path=nb_path,
                    )
                )
        if _EXPLANATION_TAG_RE.match(tag):
            explanation_tags.add(tag)
            if cell_type != "markdown":
                findings.append(
                    Finding(
                        "ERROR",
                        f"Tag {tag} must be on a markdown cell (found on {cell_type!r})",
                        path=nb_path,
                    )
                )

    if len(exercise_tags) > 1:
        findings.append(
            Finding(
                "ERROR",
                f"Cell has multiple exerciseN tags {sorted(exercise_tags)}; use exactly one exerciseN tag per graded cell",
                path=nb_path,
            )
        )
    if len(explanation_tags) > 1:
        findings.append(
            Finding(
                "ERROR",
                f"Cell has multiple explanationN tags {sorted(explanation_tags)}; use exactly one explanationN tag per reflection cell",
                path=nb_path,
            )
        )

    return exercise_tags, explanation_tags, findings


def _tag_numbers(tags: set[str], pattern: re.Pattern[str]) -> list[int]:
    nums: list[int] = []
    for tag in tags:
        match = pattern.match(tag)
        if match is None:
            continue
        nums.append(int(match.group("n")))
    return sorted(nums)


def _check_tag_continuity(
    *,
    nb_path: Path,
    exercise_tags: set[str],
    explanation_tags: set[str],
    expect_debug: bool,
) -> list[Finding]:
    findings: list[Finding] = []

    if not exercise_tags:
        findings.append(
            Finding(
                "ERROR",
                "No exerciseN tags found (expected at least exercise1)",
                path=nb_path,
            )
        )
        return findings

    if expect_debug and not explanation_tags:
        findings.append(
            Finding(
                "ERROR",
                "Debug exercise expected explanationN tag(s) but none were found",
                path=nb_path,
            )
        )

    exercise_nums = _tag_numbers(exercise_tags, _EXERCISE_TAG_RE)
    expected = list(range(1, max(exercise_nums) + 1))
    if exercise_nums != expected:
        findings.append(
            Finding(
                "ERROR",
                f"Exercise tags are not contiguous: found {exercise_nums}, expected {expected}",
                path=nb_path,
            )
        )

    if expect_debug and explanation_tags:
        exp_nums = _tag_numbers(explanation_tags, _EXPLANATION_TAG_RE)
        if exp_nums != exercise_nums:
            findings.append(
                Finding(
                    "ERROR",
                    "Debug exercise explanationN tags must exactly match exerciseN tags",
                    path=nb_path,
                )
            )

    return findings


def _check_notebook_structure(
    nb_path: Path, nb: NotebookDocument, *, expect_debug: bool
) -> list[Finding]:
    findings: list[Finding] = []

    cells = nb.get("cells")
    if not isinstance(cells, list):
        return [Finding("ERROR", "Notebook has no 'cells' list", path=nb_path)]
    cells_list = cast(list[object], cells)

    found_exercise_tags: set[str] = set()
    found_explanation_tags: set[str] = set()

    for idx, cell in enumerate(cells_list, start=1):
        if not isinstance(cell, dict):
            findings.append(Finding("ERROR", f"Cell {idx} is not an object", path=nb_path))
            continue
        cell_mapping = cast(dict[str, Any], cell)
        if not _is_notebook_cell(cell_mapping):
            findings.append(
                Finding(
                    "ERROR",
                    f"Cell {idx} has invalid notebook cell structure",
                    path=nb_path,
                )
            )
            continue

        findings.extend(_check_cell_language(idx, cell_mapping, nb_path))

        cell_type = cell_mapping.get("cell_type")
        tags = _cell_tags(cell_mapping)
        exercise_tags, explanation_tags, tag_findings = _collect_tag_findings(
            cell_type=cell_type,
            tags=tags,
            nb_path=nb_path,
        )

        found_exercise_tags.update(exercise_tags)
        found_explanation_tags.update(explanation_tags)
        findings.extend(tag_findings)

    findings.extend(
        _check_tag_continuity(
            nb_path=nb_path,
            exercise_tags=found_exercise_tags,
            explanation_tags=found_explanation_tags,
            expect_debug=expect_debug,
        )
    )

    return findings


def _progression_rules() -> dict[str, list[re.Pattern[str]]]:
    # Patterns that indicate the presence of a construct.
    # These are heuristic checks and intentionally conservative.
    return {
        "selection": [
            re.compile(r"\bif\b"),
            re.compile(r"\belif\b"),
            re.compile(r"\belse\b"),
        ],
        "iteration": [
            re.compile(r"\bfor\b"),
            re.compile(r"\bwhile\b"),
            re.compile(r"\bbreak\b"),
            re.compile(r"\bcontinue\b"),
            re.compile(r"\brange\s*\("),
        ],
        "data_types": [
            re.compile(r"\bint\s*\("),
            re.compile(r"\bfloat\s*\("),
            re.compile(r"\bstr\s*\("),
        ],
        "lists": [
            re.compile(r"\[[^\]]*\]"),
            re.compile(r"\.append\s*\("),
            re.compile(r"\blen\s*\("),
            re.compile(r"\.sort\s*\("),
        ],
        "dictionaries": [
            re.compile(r"\{[^}]*:[^}]*\}"),
            re.compile(r"\.get\s*\("),
            re.compile(r"\.items\s*\("),
        ],
        "functions": [
            re.compile(r"^\s*def\s+", re.MULTILINE),
            re.compile(r"\breturn\b"),
        ],
        "file_handling": [re.compile(r"\bopen\s*\("), re.compile(r"\bwith\s+open\b")],
        "exceptions": [
            re.compile(r"\btry\b"),
            re.compile(r"\bexcept\b"),
            re.compile(r"\braise\b"),
        ],
        "libraries": [
            re.compile(r"^\s*import\b", re.MULTILINE),
            re.compile(r"^\s*from\s+\w+\s+import\b", re.MULTILINE),
        ],
        "oop": [
            re.compile(r"^\s*class\s+", re.MULTILINE),
            re.compile(r"\bself\b\s*\."),
        ],
    }


def _index_of_construct(construct: str) -> int:
    try:
        return CONSTRUCT_ORDER.index(construct)
    except ValueError:
        return -1


def _tokenize_leniently(text: str) -> list[tokenize.TokenInfo]:
    """Tokenize ``text``, keeping the tokens emitted before any tokenizer failure.

    Debug exercises ship intentionally invalid tagged cells, so a tokenizer
    failure must not discard the tokens that were read successfully.
    ``IndentationError`` and ``TabError`` need no arm of their own: both are
    ``SyntaxError`` subclasses.
    """
    tokens: list[tokenize.TokenInfo] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            tokens.append(token)
    except (tokenize.TokenError, SyntaxError):
        pass
    return tokens


def _line_start_offsets(text: str) -> list[int]:
    """Return the absolute offset at which each line of ``text`` starts.

    The lines come from ``io.StringIO`` rather than ``str.splitlines`` because
    ``tokenize`` reads its source with ``readline``, which ends a line only at a
    newline. ``splitlines`` also breaks on ``\\r``, form feed, NEL, and the Unicode
    line and paragraph separators, so its offsets would drift away from the
    tokenizer's row numbers and blank the wrong characters.
    """
    offsets = [0]
    for line in io.StringIO(text):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _token_offset(line_offsets: list[int], position: tuple[int, int]) -> int:
    """Return the absolute offset of a tokenizer ``(row, column)`` position."""
    row, column = position
    return line_offsets[row - 1] + column


def _leaves_literal_open(tokens: list[tokenize.TokenInfo]) -> bool:
    """Return True when ``tokens`` end inside a string literal that never closed.

    An f-string missing its closing quote leaves its opening token behind and the
    tokenizer stops before emitting the rest of its literal text, so the unread
    text that follows is prose. Braces are counted as well: a replacement field's
    ``{`` is still open when the tokenizer stops inside the field's expression,
    and that unread text is real code, so an open brace must not be read as
    literal text.
    """
    literal_depth = 0
    brace_depth = 0
    for token in tokens:
        if token.type in _LITERAL_OPEN_TOKEN_TYPES:
            literal_depth += 1
        elif token.type in _LITERAL_CLOSE_TOKEN_TYPES:
            literal_depth -= 1
        elif token.type == tokenize.OP:
            if token.string == "{":
                brace_depth += 1
            elif token.string == "}":
                brace_depth -= 1
    return literal_depth > 0 and brace_depth == 0


def _unfinished_literal_offset(
    line_offsets: list[int],
    text: str,
    tokens: list[tokenize.TokenInfo],
) -> int | None:
    """Return the offset an unfinished string literal's unread text starts at.

    Returns ``None`` when the tokenizer's failure left real code unread, so that
    text stays scannable and can only add a warning, never hide one. That is the
    case for an ``IndentationError``, which stops at the line whose indentation
    does not match the block above it, and for an unclosed bracket, which stops
    at the end of the input with the rest of the statement still unread.

    The unread text starts where the last emitted token ended, or at the start of
    the cell when the very first token already failed. It is the body of an
    unfinished literal when the unread text opens a literal itself, so the
    tokenizer failed on a literal it never emitted a token for, or when the
    emitted tokens leave an f-string open.
    """
    offset = _token_offset(line_offsets, tokens[-1].end) if tokens else 0
    if _STRING_OPENING_RE.match(text, offset) is not None or _leaves_literal_open(tokens):
        return offset
    return None


def _blank_span(chars: list[str], start: int, end: int) -> None:
    """Overwrite ``chars[start:end]`` with spaces, keeping any line breaks."""
    for index in range(start, end):
        if chars[index] != "\n":
            chars[index] = " "


def _executable_source(text: str) -> str:
    """Return ``text`` with comment and string/f-string literal text blanked out.

    Offsets and line breaks are preserved so the progression patterns keep
    matching the original source layout. Executable code inside an f-string
    replacement field survives, because since Python 3.12 (PEP 701) ``tokenize``
    emits a replacement field as ordinary tokens while only the literal chunks
    become f-string tokens. Before 3.12 the whole f-string arrives as one string
    token, so its replacement fields are blanked with it.

    Debug exercises ship intentionally invalid tagged cells, so a tokenizer
    failure keeps the tokens read before the failure instead of skipping the
    cell. A literal the tokenizer could not close is the one case that yields no
    token to blank, so its unread text is blanked to the end of the cell; the
    tokens emitted before the failure are real code and are still scanned.
    """
    chars = list(text)
    line_offsets = _line_start_offsets(text)
    tokens = _tokenize_leniently(text)
    for token in tokens:
        if token.type in _EXECUTABLE_TOKEN_TYPES:
            continue
        _blank_span(
            chars,
            _token_offset(line_offsets, token.start),
            _token_offset(line_offsets, token.end),
        )
    unfinished_literal = _unfinished_literal_offset(line_offsets, text, tokens)
    if unfinished_literal is not None:
        _blank_span(chars, unfinished_literal, len(chars))
    return "".join(chars)


def _scan_for_progression_violations(  # noqa: C901
    *,
    text: str,
    allowed_construct: str,
    path: Path,
) -> list[Finding]:
    findings: list[Finding] = []

    rules = _progression_rules()
    allowed_idx = _index_of_construct(allowed_construct)
    if allowed_idx < 0:
        return [
            Finding(
                "WARN",
                f"Unknown construct: {allowed_construct!r} (skipping progression checks)",
                path=path,
            )
        ]

    # Comments and printed string text are prose, so only executable source counts.
    executable_text = _executable_source(text)

    # If we're in construct K, then constructs strictly after K are disallowed.
    disallowed = CONSTRUCT_ORDER[allowed_idx + 1 :]

    for construct in disallowed:
        if construct == "data_types" and allowed_construct in _CASTING_PREREQUISITE_CONSTRUCTS:
            continue
        for pat in rules.get(construct, []):
            # Special-case: allow a single top-level `def solve()` wrapper (and returns inside it)
            if construct == "functions":
                func_defs = list(
                    re.finditer(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", executable_text, re.M)
                )
                # If there are any named functions other than `solve`, report as before
                other_funcs = [m for m in func_defs if m.group(1) != "solve"]
                if other_funcs:
                    findings.append(
                        Finding(
                            "WARN",
                            f"Possible progression violation: found {construct} pattern {pat.pattern!r}",
                            path=path,
                        )
                    )
                    break
                # If pattern is the def pattern and only `solve` exists, skip warning
                if pat.pattern == r"^\s*def\s+" and func_defs:
                    continue
                # If pattern is the return pattern, ensure all returns are inside solve()
                if pat.pattern == r"\breturn\b" and func_defs:
                    # Build solve() regions and ensure every 'return' is inside some solve() region
                    regions: list[tuple[int, int]] = []
                    for idx, m in enumerate(func_defs):
                        s = m.start()
                        e = (
                            func_defs[idx + 1].start()
                            if idx + 1 < len(func_defs)
                            else len(executable_text)
                        )
                        regions.append((s, e))
                    return_positions = [
                        m.start() for m in re.finditer(r"\breturn\b", executable_text)
                    ]
                    if return_positions and all(
                        any(s <= pos < e for s, e in regions) for pos in return_positions
                    ):
                        continue
                # otherwise fallthrough to regular warning

            if pat.search(executable_text):
                findings.append(
                    Finding(
                        "WARN",
                        f"Possible progression violation: found {construct} pattern {pat.pattern!r}",
                        path=path,
                    )
                )
                break

    return findings


def _collect_code_cell_text(nb: NotebookDocument) -> str:
    """Collect source text from code cells that have an ``exerciseN`` tag.

    Only cells tagged with ``exercise1``, ``exercise2``, etc. are included.
    Untagged infrastructure cells (scratch, self-checker) are excluded to
    avoid false-positive progression warnings.
    """
    cells = nb.get("cells")
    if not isinstance(cells, list):
        return ""
    code_chunks: list[str] = []
    for cell in cells:
        if not _is_notebook_cell(cell):
            continue
        cell_type = cell.get("cell_type")
        if cell_type != "code":
            continue
        tags = _cell_tags(cell)
        if not any(_EXERCISE_TAG_RE.match(tag) for tag in tags):
            continue
        code_chunks.append(_cell_source_text(cell))
    return "\n\n".join(code_chunks)


def _collect_notebook_tag_sets(nb: NotebookDocument) -> tuple[set[str], set[str]]:
    """Return exerciseN and explanationN tag sets found in a notebook."""
    exercise_tags: set[str] = set()
    explanation_tags: set[str] = set()
    cells = nb.get("cells")
    if not isinstance(cells, list):
        return exercise_tags, explanation_tags

    for cell in cells:
        if not _is_notebook_cell(cell):
            continue
        tags = _cell_tags(cell)
        exercise_tags.update(tag for tag in tags if _EXERCISE_TAG_RE.match(tag))
        explanation_tags.update(tag for tag in tags if _EXPLANATION_TAG_RE.match(tag))
    return exercise_tags, explanation_tags


def _check_student_solution_notebook_parity(
    *,
    student_nb: NotebookDocument,
    solution_nb: NotebookDocument,
    solution_path: Path,
) -> list[Finding]:
    """Ensure the student and solution notebooks expose the same tagged exercise surface."""
    findings: list[Finding] = []
    student_exercise_tags, student_explanation_tags = _collect_notebook_tag_sets(student_nb)
    solution_exercise_tags, solution_explanation_tags = _collect_notebook_tag_sets(solution_nb)

    if student_exercise_tags != solution_exercise_tags:
        findings.append(
            Finding(
                "ERROR",
                "Student and solution notebooks must use the same exerciseN tags",
                path=solution_path,
            )
        )
    if student_explanation_tags != solution_explanation_tags:
        findings.append(
            Finding(
                "ERROR",
                "Student and solution notebooks must use the same explanationN tags",
                path=solution_path,
            )
        )

    return findings


def _print_findings(findings: list[Finding]) -> None:
    for f in findings:
        loc = f" ({f.path})" if f.path else ""
        print(f"{f.severity}: {f.message}{loc}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "exercise_key",
        nargs="?",
        help="Canonical exercise identifier, for example ex004_sequence_debug_syntax. "
        "Required unless --all is given.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Verify every exercise under <repo-root>/exercises/<construct>/ and report "
        "one labelled section per exercise_key",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: auto-detected)",
    )
    parser.add_argument(
        "--construct",
        choices=CONSTRUCT_ORDER,
        default=None,
        help="Construct to validate progression against (default: inferred from canonical "
        "metadata). Single-exercise mode only; rejected with --all.",
    )
    parser.add_argument(
        "--type",
        choices=["debug", "modify", "make", "gaps"],
        default=None,
        help="Exercise type (default: inferred from canonical metadata). "
        "Single-exercise mode only; rejected with --all.",
    )
    parser.add_argument(
        "--skip-empty-checks",
        action="store_true",
        default=False,
        help="Suppress the empty-CHECKS error in Gate F, allowing the verifier "
        "to be used during Phase 1 (notebook authoring) before checker "
        "definitions are written",
    )
    return parser


def _resolve_exercise_context(
    *,
    repo_root: Path,
    slug: str,
) -> tuple[Path | None, str | None, str | None, _ExerciseMetadataError | None, list[Finding]]:
    exercises_root = repo_root / "exercises"
    inferred_construct: str | None = None
    inferred_type: str | None = None
    metadata_error: _ExerciseMetadataError | None = None
    findings: list[Finding] = []

    try:
        ex_dir = resolve_exercise_dir(slug, exercises_root)
    except (LookupError, TypeError) as exc:
        findings.append(
            Finding(
                "ERROR",
                f"Could not resolve canonical exercise directory for {slug!r}: {exc}",
                path=exercises_root,
            )
        )
        return None, inferred_construct, inferred_type, metadata_error, findings

    try:
        inferred_construct, inferred_type = _load_construct_and_type(ex_dir)
    except _ExerciseMetadataError as exc:
        metadata_error = exc
        findings.append(Finding("ERROR", str(exc), path=exc.path))

    return ex_dir, inferred_construct, inferred_type, metadata_error, findings


def _collect_teacher_findings(
    *,
    construct: str | None,
    ex_dir: Path | None,
    metadata_error: _ExerciseMetadataError | None,
    notebook_name: str,
    repo_root: Path,
) -> list[Finding]:
    if ex_dir is None:
        return []

    findings = _check_canonical_structure(ex_dir)
    if metadata_error is None or construct is not None:
        findings.extend(
            _check_order_of_teaching(
                ex_dir,
                construct=construct,
                repo_root=repo_root,
                notebook_name=notebook_name,
            )
        )
    return findings


def _load_solution_notebook(
    *,
    ex_dir: Path | None,
    expect_debug: bool,
) -> tuple[Path, NotebookDocument | None, list[Finding]]:
    nb_solution_path = (
        ex_dir / "notebooks" / "solution.ipynb" if ex_dir is not None else Path("solution.ipynb")
    )
    if not nb_solution_path.exists():
        return nb_solution_path, None, []

    nb_solution = _load_notebook(nb_solution_path)
    findings = _check_notebook_structure(
        nb_solution_path,
        nb_solution,
        expect_debug=expect_debug,
    )
    return nb_solution_path, nb_solution, findings


def _collect_progression_findings(
    *,
    construct: str | None,
    nb_path: Path,
    nb_solution: NotebookDocument | None,
    nb_solution_path: Path,
    nb_student: NotebookDocument,
) -> list[Finding]:
    if construct is None:
        return []

    findings = _scan_for_progression_violations(
        text=_collect_code_cell_text(nb_student),
        allowed_construct=construct,
        path=nb_path,
    )
    if nb_solution is not None:
        findings.extend(
            _scan_for_progression_violations(
                text=_collect_code_cell_text(nb_solution),
                allowed_construct=construct,
                path=nb_solution_path,
            )
        )
    return findings


# -- Gates F-I: student checker support, expectations, variant overrides, runtime self-check --


def _load_exercise_local_module(ex_dir: Path, module_name: str) -> object | None:
    """Import an exercise-local test module by file path.

    Uses direct file import rather than the runtime resolver so that the
    verifier works with unregistered exercises (e.g. during scaffolding).
    Returns ``None`` if the module does not exist or cannot be imported.
    """
    module_path = ex_dir / "tests" / f"{module_name}.py"
    if not module_path.is_file():
        return None

    import importlib.util

    qualified_name = f"_verify_local_{ex_dir.name}_{module_name}"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    if spec is None or spec.loader is None:
        return None

    import sys as _sys

    module = importlib.util.module_from_spec(spec)
    _sys.modules[qualified_name] = module
    try:
        spec.loader.exec_module(module)
    except (SyntaxError, ImportError, NameError, AttributeError, TypeError):
        _sys.modules.pop(qualified_name, None)
        return None
    return module


def _check_student_checker_support(
    ex_dir: Path,
    *,
    skip_empty_checks: bool = False,
) -> list[Finding]:
    """Gate F: Verify student_checker_support.py exists with non-empty CHECKS.

    Args:
        ex_dir: Exercise directory path.
        skip_empty_checks: When True, suppress the empty-CHECKS error so the
            verifier can be used during Phase 1 (notebook authoring) before
            checker definitions are written.
    """
    findings: list[Finding] = []
    checker_path = ex_dir / "tests" / "student_checker_support.py"

    if not checker_path.exists():
        findings.append(
            Finding(
                "ERROR",
                "Missing student_checker_support.py",
                path=checker_path,
            )
        )
        return findings

    module = _load_exercise_local_module(ex_dir, "student_checker_support")
    if module is None:
        findings.append(
            Finding(
                "ERROR",
                "student_checker_support.py could not be imported",
                path=checker_path,
            )
        )
        return findings

    checks = getattr(module, "CHECKS", None)
    if checks is None or not isinstance(checks, list):
        findings.append(
            Finding(
                "ERROR",
                "student_checker_support.py must define CHECKS as a list",
                path=checker_path,
            )
        )
    elif not checks and not skip_empty_checks:
        findings.append(
            Finding(
                "ERROR",
                "CHECKS list in student_checker_support.py is empty; "
                "author must define check functions",
                path=checker_path,
            )
        )

    return findings


@dataclass(frozen=True)
class _ExpectationDicts:
    """The recognised expectation dicts of one ``expectations.py`` module.

    Attributes:
        static: Dicts declaring what a part prints without reading input.
        interactive: Dicts declaring a runnable input case, or the
            prompts/inputs/post-input message it is driven with, for a part
            whose code calls ``input()``.
    """

    static: dict[str, dict[int, object]]
    interactive: dict[str, dict[int, object]]


def _expectation_convention(name: str) -> str | None:
    """Return the convention suffix of an ``EX<N>_<CONVENTION>`` name, else ``None``."""
    match = _EXPECTATION_NAME_RE.match(name)
    if match is None:
        return None
    return match.group("convention")


def _collect_expectation_dicts(module: object) -> _ExpectationDicts:
    """Split the module's recognised expectation dicts into static and interactive."""
    static: dict[str, dict[int, object]] = {}
    interactive: dict[str, dict[int, object]] = {}

    for name in dir(module):
        value = getattr(module, name)
        if not isinstance(value, dict):
            continue
        convention = _expectation_convention(name)
        if convention is None:
            continue
        typed = cast(dict[int, object], value)
        if convention in _INTERACTIVE_EXPECTATION_CONVENTIONS:
            interactive[name] = typed
        elif convention in _STATIC_EXPECTATION_CONVENTIONS:
            static[name] = typed

    return _ExpectationDicts(static=static, interactive=interactive)


def _declared_parts(dicts: dict[str, dict[int, object]]) -> set[int]:
    """Return the union of the exercise numbers declared by ``dicts``."""
    parts: set[int] = set()
    for declared in dicts.values():
        parts.update(declared)
    return parts


def _module_level_assignment(node: ast.stmt) -> tuple[str, ast.expr] | None:
    """Return ``(name, value)`` for a simple module-level assignment, else ``None``."""
    if isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.value is not None:
            return node.target.id, node.value
        return None
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id, node.value
    return None


def _mirrored_case_name(node: ast.expr) -> str | None:
    """Return the name whose ``expected_output`` ``node`` reads, if that is all it reads.

    ``case["expected_output"]`` and ``case.expected_output`` are the two audited ways
    a shipped mirror reads an input case. Any other expression — a concatenation,
    an f-string, or a different case field — derives new values instead of
    mirroring them.
    """
    base: ast.expr
    if isinstance(node, ast.Attribute):
        base = node.value
        reads_expected_output = node.attr == _EXPECTED_OUTPUT_KEY
    elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        base = node.value
        reads_expected_output = node.slice.value == _EXPECTED_OUTPUT_KEY
    else:
        return None
    if not reads_expected_output or not isinstance(base, ast.Name):
        return None
    return base.id


def _target_names(target: ast.expr) -> set[str]:
    """Return the names a comprehension or ``for`` target binds."""
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for element in target.elts:
            names |= _target_names(element)
        return names
    return set()


def _mirrors_input_cases(comp: ast.DictComp, source_names: set[str]) -> bool:
    """Return True when ``comp`` copies each input case's ``expected_output`` value.

    Keying a dict from the input cases is not enough to make it a mirror: the
    values must be the cases' ``expected_output`` unchanged. A comprehension that
    derives anything else from the cases is a second, independent declaration.
    """
    if len(comp.generators) != 1:
        return False
    generator = comp.generators[0]
    iterates_input_cases = any(
        isinstance(node, ast.Name) and node.id in source_names for node in ast.walk(generator.iter)
    )
    if not iterates_input_cases:
        return False
    case_name = _mirrored_case_name(comp.value)
    return case_name is not None and case_name in _target_names(generator.target)


def _reference_alias_names(expectations_path: Path, source_names: set[str]) -> set[str]:
    """Return the dict names that mirror ``source_names`` value for value.

    An entirely interactive exercise may publish a quick-reference
    ``EX<N>_EXPECTED_OUTPUTS`` computed from ``EX<N>_INPUT_CASES``. Such a dict is
    a reference alias rather than a second, static declaration, so it must not be
    reported as an exercise being listed in both families. A hand-written literal
    dict, and a comprehension that derives new values from the input cases, are
    independent declarations and are still reported.
    """
    tree = ast.parse(expectations_path.read_text(encoding="utf-8"))

    aliases: set[str] = set()
    for node in tree.body:
        assignment = _module_level_assignment(node)
        if assignment is None:
            continue
        name, value = assignment
        if isinstance(value, ast.DictComp) and _mirrors_input_cases(value, source_names):
            aliases.add(name)
    return aliases


@dataclass(frozen=True)
class _DeclaredFamilyParts:
    """The exercise numbers one ``expectations.py`` declares per family.

    Attributes:
        static: Parts declared by a static dict, excluding reference aliases.
        interactive: Parts declared by an interactive input-case dict.
    """

    static: set[int]
    interactive: set[int]


def _declared_family_parts(
    expectations_path: Path,
    expectations: _ExpectationDicts,
) -> _DeclaredFamilyParts:
    """Return the parts each expectation family declares, reference aliases excluded.

    This is the single definition of the static/interactive split, so callers
    that classify an exercise's declarations share the verifier's own answer.
    """
    alias_names = _reference_alias_names(expectations_path, set(expectations.interactive))
    static = _declared_parts(
        {name: value for name, value in expectations.static.items() if name not in alias_names}
    )
    return _DeclaredFamilyParts(
        static=static,
        interactive=_declared_parts(expectations.interactive),
    )


def _check_expectations_module(ex_dir: Path, parts: int) -> list[Finding]:
    """Gate G: Verify expectations.py covers every part with a runnable expectation.

    Coverage is the union of the part keys the static and interactive families
    declare, so an exercise may split its expectations across static, interactive,
    and shape-specific dicts as long as every part 1..parts is declared by one of
    them. A reference alias declares no part of its own: it only republishes the
    input cases it is derived from, which are counted once, through that input
    case dict.
    """
    findings: list[Finding] = []
    expectations_path = ex_dir / "tests" / "expectations.py"

    if not expectations_path.exists():
        findings.append(
            Finding(
                "ERROR",
                "Missing expectations.py",
                path=expectations_path,
            )
        )
        return findings

    module = _load_exercise_local_module(ex_dir, "expectations")
    if module is None:
        findings.append(
            Finding(
                "ERROR",
                "expectations.py could not be imported",
                path=expectations_path,
            )
        )
        return findings

    expectations = _collect_expectation_dicts(module)
    if not expectations.static and not expectations.interactive:
        findings.append(
            Finding(
                "ERROR",
                "expectations.py must define at least one recognised expectation dict "
                "(for example EX<N>_EXPECTED_OUTPUTS, EX<N>_EXPECTED_STATIC_OUTPUTS, "
                "or EX<N>_INPUT_CASES)",
                path=expectations_path,
            )
        )
        return findings

    declared = _declared_family_parts(expectations_path, expectations)
    covered_parts = declared.static | declared.interactive
    if not covered_parts:
        findings.append(
            Finding(
                "ERROR",
                f"expectation dicts are all empty; expected coverage for 1..{parts}",
                path=expectations_path,
            )
        )
        return findings

    missing_keys = set(range(1, parts + 1)) - covered_parts
    if missing_keys:
        findings.append(
            Finding(
                "ERROR",
                f"expectation dicts are missing keys for parts {sorted(missing_keys)}; "
                f"expected 1..{parts}",
                path=expectations_path,
            )
        )

    return findings


def _detect_interactive_exercises(nb: NotebookDocument) -> set[int]:  # noqa: C901
    """Return exercise numbers whose tagged code cells contain ``input()`` calls.

    The detection is heuristic (a regex for ``input(``) and may false-positive
    on ``input`` inside comments or strings, which is acceptable for a
    lint-style verifier.
    """
    interactive: set[int] = set()
    cells = nb.get("cells")
    if not isinstance(cells, list):
        return interactive
    for cell in cells:
        if not _is_notebook_cell(cell):
            continue
        if cell.get("cell_type") != "code":
            continue
        tags = _cell_tags(cell)
        exercise_tags = [t for t in tags if _EXERCISE_TAG_RE.match(t)]
        if not exercise_tags:
            continue
        source = _cell_source_text(cell)
        if _INPUT_CALL_RE.search(source):
            for tag in exercise_tags:
                m = _EXERCISE_TAG_RE.match(tag)
                if m:
                    interactive.add(int(m.group("n")))
    return interactive


def _classify_declaration(
    *,
    ex_no: int,
    uses_input: bool,
    in_static: bool,
    in_interactive: bool,
) -> tuple[str, str] | None:
    """Return the ``(severity, message)`` for one part's misclassification.

    Returns:
        ``None`` when the part's static/interactive declaration agrees with the
        notebook.
    """
    if uses_input and not in_interactive:
        if in_static:
            return (
                "ERROR",
                f"Exercise {ex_no} uses input() in the notebook but is declared only "
                f"in static expectation dicts — this will cause the runtime self-check "
                f"to hang.  Declare exercise {ex_no} in EX<N>_INPUT_CASES (or the "
                f"interactive expectation dict this exercise uses) instead.",
            )
        return (
            "ERROR",
            f"Exercise {ex_no} uses input() in the notebook but is not declared in any "
            f"interactive expectation dict, for example EX<N>_INPUT_CASES, in "
            f"expectations.py.",
        )
    if uses_input and in_static:
        return (
            "WARN",
            f"Exercise {ex_no} is listed in both a static expectation dict and an "
            f"interactive input-case dict in expectations.py — it should only appear "
            f"in one.",
        )
    if not uses_input and in_interactive:
        return (
            "ERROR",
            f"Exercise {ex_no} does not use input() in the notebook but is declared in "
            f"an interactive expectation dict, for example EX<N>_INPUT_CASES, in "
            f"expectations.py.",
        )
    return None


def _check_expectations_input_consistency(
    *,
    ex_dir: Path,
    nb_solution: NotebookDocument,
    parts: int,
) -> list[Finding]:
    """Cross-check the expectations.py static/interactive split against ``input()`` usage.

    Any exercise whose code cell uses ``input()`` must be declared by an
    interactive expectation dict, not only by a static one.  Conversely, exercises
    that do **not** use ``input()`` must not be declared interactive.

    Without this check the runtime self-check (Gate I) will hang because
    ``run_cell_and_capture_output`` provides no stdin and the cell blocks
    forever on ``input()``.
    """
    findings: list[Finding] = []
    expectations_path = ex_dir / "tests" / "expectations.py"

    module = _load_exercise_local_module(ex_dir, "expectations")
    if module is None:
        return findings  # Gate G already reports the import error

    expectations = _collect_expectation_dicts(module)
    declared = _declared_family_parts(expectations_path, expectations)

    interactive_exercises = _detect_interactive_exercises(nb_solution)

    for ex_no in range(1, parts + 1):
        classification = _classify_declaration(
            ex_no=ex_no,
            uses_input=ex_no in interactive_exercises,
            in_static=ex_no in declared.static,
            in_interactive=ex_no in declared.interactive,
        )
        if classification is not None:
            severity, message = classification
            findings.append(Finding(severity, message, path=expectations_path))

    return findings


def _check_notebook_variant_overrides(
    *,
    ex_dir: Path,
    student_nb: NotebookDocument,
    solution_nb: NotebookDocument,
) -> list[Finding]:
    """Gate H: Verify variant overrides in student and solution notebooks.

    Policy: a student self-checker cell may omit the ``PYTUTOR_ACTIVE_VARIANT``
    assignment because the checker runtime already defaults to the student
    variant when the variable is unset, which is what the scaffolder emits. An
    explicitly wrong student assignment stays a WARN, and a missing or wrong
    solution assignment stays an ERROR because that cell would otherwise read
    ``student.ipynb`` instead of ``solution.ipynb``.
    """
    findings: list[Finding] = []

    student_nb_path = ex_dir / "notebooks" / "student.ipynb"
    solution_nb_path = ex_dir / "notebooks" / "solution.ipynb"

    # Check student notebook: only an explicit wrong variant is a finding, since
    # an absent assignment resolves to 'student' through the runtime default.
    student_variant = _find_variant_in_notebook(student_nb)
    if student_variant is not None and student_variant != "student":
        findings.append(
            Finding(
                "WARN",
                "Student notebook self-checker sets PYTUTOR_ACTIVE_VARIANT "
                f"to {student_variant!r} instead of 'student'",
                path=student_nb_path,
            )
        )

    # Check solution notebook
    solution_variant = _find_variant_in_notebook(solution_nb)
    if solution_variant is None:
        findings.append(
            Finding(
                "ERROR",
                "Solution notebook self-checker cell does not set "
                "PYTUTOR_ACTIVE_VARIANT — it will default to 'student' and "
                "read from student.ipynb instead of solution.ipynb",
                path=solution_nb_path,
            )
        )
    elif solution_variant != "solution":
        findings.append(
            Finding(
                "ERROR",
                "Solution notebook self-checker sets PYTUTOR_ACTIVE_VARIANT "
                f"to {solution_variant!r} instead of 'solution'",
                path=solution_nb_path,
            )
        )

    return findings


# Match PYTUTOR_ACTIVE_VARIANT assignment, accounting for optional quote
# characters between VARIANT and ] (e.g. os.environ["VARIANT"] = "value").
VAR_OVERRIDE_RE = re.compile(
    r"""PYTUTOR_ACTIVE_VARIANT['"]?\]\s*=\s*(?P<quote>['"])(?P<value>.*?)(?P=quote)"""
)


def _find_variant_in_notebook(nb: NotebookDocument) -> str | None:
    """Return the PYTUTOR_ACTIVE_VARIANT value from a notebook, or None."""
    cells = nb.get("cells", [])
    for cell in cells:
        if not _is_notebook_cell(cell):
            continue
        match = VAR_OVERRIDE_RE.search(_cell_source_text(cell))
        if match:
            return match.group("value")
    return None


def _check_runtime_self_check(
    *,
    ex_dir: Path,
    exercise_key: str,
) -> list[Finding]:
    """Gate I: Run self-checker against solution variant and report failures."""
    findings: list[Finding] = []

    from exercise_runtime_support.execution_variant import configure_variant_environment
    from exercise_runtime_support.student_checker.checks import (
        run_exercise_checks,
    )

    # Check if student_checker_support.py exists (already validated by Gate F,
    # but Gate I may be called independently)
    checker_path = ex_dir / "tests" / "student_checker_support.py"
    if not checker_path.exists():
        findings.append(
            Finding(
                "WARN",
                "Cannot run runtime self-check: student_checker_support.py missing",
                path=checker_path,
            )
        )
        return findings

    # Save current variant and set to solution
    original_variant = os.environ.get("PYTUTOR_ACTIVE_VARIANT")
    configure_variant_environment(os.environ, "solution")

    try:
        results = run_exercise_checks(exercise_key)
        for result in results:
            if not result.passed:
                findings.append(
                    Finding(
                        "ERROR",
                        f"Self-check failed for exercise {result.exercise_no} "
                        f"({result.title}): {', '.join(result.issues)}",
                        path=checker_path,
                    )
                )
    except (ImportError, LookupError, ValueError) as exc:
        findings.append(
            Finding(
                "ERROR",
                f"Runtime self-check raised an exception: {exc}",
                path=checker_path,
            )
        )
    finally:
        # Restore original variant
        if original_variant is not None:
            os.environ["PYTUTOR_ACTIVE_VARIANT"] = original_variant
        elif "PYTUTOR_ACTIVE_VARIANT" in os.environ:
            del os.environ["PYTUTOR_ACTIVE_VARIANT"]

    return findings


def _summarise(findings: list[Finding]) -> int:
    """Print the aggregate OK/FAIL line for ``findings`` and return the exit code."""
    error_count = sum(1 for f in findings if f.severity == "ERROR")
    warn_count = sum(1 for f in findings if f.severity == "WARN")

    if error_count:
        print(f"\nFAIL: {error_count} error(s), {warn_count} warning(s)")
        return 1

    print(f"\nOK: {warn_count} warning(s)")
    return 0


def _report_findings(findings: list[Finding]) -> int:
    _print_findings(findings)
    return _summarise(findings)


def _run_exercise_gates(  # noqa: C901
    *,
    findings: list[Finding],
    repo_root: Path,
    slug: str,
    options: _VerifyOptions,
) -> None:
    """Append every gate finding for one exercise to ``findings``.

    ``findings`` is supplied by the caller so that findings already collected
    survive a later abort (see :func:`_verify_exercise`).
    """
    ex_dir, inferred_construct, inferred_type, metadata_error, resolution_findings = (
        _resolve_exercise_context(
            repo_root=repo_root,
            slug=slug,
        )
    )
    findings.extend(resolution_findings)
    # _resolve_exercise_context() records the user-facing error in findings and
    # returns None here when the canonical exercise directory cannot be resolved.
    if ex_dir is None:
        return

    nb_path = ex_dir / "notebooks" / "student.ipynb"
    construct = options.construct or inferred_construct
    ex_type = options.exercise_type or inferred_type

    findings.extend(
        _collect_teacher_findings(
            construct=construct,
            ex_dir=ex_dir,
            metadata_error=metadata_error,
            notebook_name=nb_path.name,
            repo_root=repo_root,
        )
    )

    nb_student = _load_notebook(nb_path)
    expect_debug = ex_type == "debug"
    findings.extend(_check_notebook_structure(nb_path, nb_student, expect_debug=expect_debug))

    nb_solution_path, nb_solution, solution_findings = _load_solution_notebook(
        ex_dir=ex_dir,
        expect_debug=expect_debug,
    )
    findings.extend(solution_findings)
    if nb_solution is not None:
        findings.extend(
            _check_student_solution_notebook_parity(
                student_nb=nb_student,
                solution_nb=nb_solution,
                solution_path=nb_solution_path,
            )
        )

    if construct is None:
        if metadata_error is None:
            findings.append(
                Finding(
                    "WARN",
                    "Could not infer construct; pass --construct to enable progression checks",
                    path=nb_path,
                )
            )
    else:
        findings.extend(
            _collect_progression_findings(
                construct=construct,
                nb_path=nb_path,
                nb_solution=nb_solution,
                nb_solution_path=nb_solution_path,
                nb_student=nb_student,
            )
        )

    # -- Gates F-I (only when metadata is valid) ----------------------------
    if metadata_error is None:
        parts = 1
        try:
            metadata = _load_canonical_metadata(ex_dir)
            parts = int(metadata.get("parts", 1))
        except _ExerciseMetadataError:
            parts = 1

        findings.extend(
            _check_student_checker_support(
                ex_dir,
                skip_empty_checks=options.skip_empty_checks,
            ),
        )
        findings.extend(_check_expectations_module(ex_dir, parts))

        if nb_solution is not None:
            input_consistency_findings = _check_expectations_input_consistency(
                ex_dir=ex_dir,
                nb_solution=nb_solution,
                parts=parts,
            )
            findings.extend(input_consistency_findings)

            findings.extend(
                _check_notebook_variant_overrides(
                    ex_dir=ex_dir,
                    student_nb=nb_student,
                    solution_nb=nb_solution,
                )
            )

            # Skip runtime self-check (Gate I) when input-consistency errors
            # are present — calling run_cell_and_capture_output on a cell
            # that uses input() but is classified as static would hang.
            has_input_errors = any(f.severity == "ERROR" for f in input_consistency_findings)
            if has_input_errors:
                findings.append(
                    Finding(
                        "WARN",
                        "Skipping runtime self-check (Gate I) because "
                        "expectations.py misclassifies interactive exercises "
                        "as static — fix the input-consistency errors above "
                        "first to prevent a hang.",
                        path=ex_dir / "tests" / "student_checker_support.py",
                    )
                )
            else:
                findings.extend(
                    _check_runtime_self_check(
                        ex_dir=ex_dir,
                        exercise_key=slug,
                    )
                )


def _verify_exercise(
    *,
    repo_root: Path,
    slug: str,
    options: _VerifyOptions,
    recover_notebook_errors: bool = False,
) -> list[Finding]:
    """Run the full gate set for one exercise and return its findings.

    During a sweep, convert notebook-load failures to findings so another
    exercise can still be verified. Single-key mode retains its original error.
    """
    findings: list[Finding] = []
    try:
        _run_exercise_gates(
            findings=findings,
            repo_root=repo_root,
            slug=slug,
            options=options,
        )
    except SystemExit as exc:
        if not recover_notebook_errors:
            raise
        findings.append(Finding("ERROR", str(exc)))
    return findings


def _discover_exercise_dirs(exercises_root: Path) -> list[Path]:
    """Return the canonical exercise directories under ``exercises_root``.

    Discovery is directory-based rather than metadata-based: every directory
    named like a canonical ``exercise_key`` directly beneath a construct
    directory is returned, so an exercise with missing or invalid
    ``exercise.json`` is still swept and reported. Directories that are not
    exercises (``additional-resources`` and friends) are left out. The result is
    sorted by ``exercise_key`` so a sweep reports the same order every run.

    Raises:
        FileNotFoundError: If ``exercises_root`` does not exist.
    """
    return sorted(
        (
            candidate
            for construct_dir in exercises_root.iterdir()
            if construct_dir.is_dir()
            for candidate in construct_dir.iterdir()
            if candidate.is_dir() and _EXERCISE_DIR_RE.match(candidate.name)
        ),
        key=lambda ex_dir: ex_dir.name,
    )


def _sweep_all_exercises(
    *,
    repo_root: Path,
    skip_empty_checks: bool,
) -> int:
    """Verify every discovered exercise and return one aggregate exit code.

    Each exercise is labelled before its own findings so a reported finding is
    always attributable to an exercise_key. The exit code is non-zero only when
    at least one exercise produced an ERROR.
    """
    exercises_root = repo_root / "exercises"
    exercise_dirs = _discover_exercise_dirs(exercises_root)
    print(f"Sweeping {len(exercise_dirs)} exercise(s) under {exercises_root}")
    if not exercise_dirs:
        return _report_findings([Finding("ERROR", "No exercises discovered", path=exercises_root)])

    findings: list[Finding] = []
    for ex_dir in exercise_dirs:
        slug = ex_dir.name
        print(f"\n=== {slug} ===")
        exercise_findings = _verify_exercise(
            repo_root=repo_root,
            slug=slug,
            options=_VerifyOptions(skip_empty_checks=skip_empty_checks),
            recover_notebook_errors=True,
        )
        _print_findings(exercise_findings)
        findings.extend(exercise_findings)

    return _summarise(findings)


def main(argv: list[str] | None = None) -> int:
    """Verify one exercise or sweep all canonical exercises via ``--all``."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.all:
        if args.exercise_key is not None:
            parser.error("--all cannot be combined with an exercise_key; pass one or the other")
        if args.construct is not None or args.type is not None:
            parser.error(
                "--all cannot be combined with --construct or --type; those overrides "
                "apply to a single exercise_key and would misreport the other exercises"
            )
        return _sweep_all_exercises(
            repo_root=args.repo_root,
            skip_empty_checks=args.skip_empty_checks,
        )

    if args.exercise_key is None:
        parser.error("provide an exercise_key, or --all to verify the whole catalogue")

    return _report_findings(
        _verify_exercise(
            repo_root=args.repo_root,
            slug=args.exercise_key,
            options=_VerifyOptions(
                construct=args.construct,
                exercise_type=args.type,
                skip_empty_checks=args.skip_empty_checks,
            ),
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
