#!/usr/bin/env python3
"""Lightweight verifier for newly generated exercises.

This script is intentionally stdlib-only. It supports the Exercise Verifier
agent by performing fast, objective checks:
- Notebook structure: metadata.language, code-vs-tag consistency
- Presence of expected tags (exerciseN, explanationN)
- Basic concept progression scanning (heuristic keyword checks)
- Presence of teacher-facing files (README/OVERVIEW) under exercises/
- Construct teaching order updated (exercises/<construct>/OrderOfTeaching.md)

It is not a replacement for reading the exercise prompts.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict, TypeGuard, cast

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

MIN_REL_PARTS = 3


@dataclass(frozen=True)
class Finding:
    severity: str  # "ERROR" or "WARN"
    message: str
    path: Path | None = None


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
        raise SystemExit(
            f"Notebook {path} is missing a top-level 'cells' list.")
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


def _infer_exercise_slug_from_notebook(notebook_path: Path) -> str | None:
    name = notebook_path.name
    if not name.endswith(".ipynb"):
        return None
    return name.removesuffix(".ipynb")


def _find_exercise_dir(ex_slug: str, repo_root: Path) -> Path | None:
    # Expected: exercises/<construct>/<type>/<ex_slug>/
    exercises_root = repo_root / "exercises"
    if not exercises_root.exists():
        return None

    candidates = [p for p in exercises_root.rglob(ex_slug) if p.is_dir()]
    # Prefer the fully-qualified construct/type layout
    for p in candidates:
        rel = p.relative_to(exercises_root)
        if len(rel.parts) >= MIN_REL_PARTS:
            return p
    return candidates[0] if candidates else None


def _infer_construct_and_type(ex_dir: Path) -> tuple[str | None, str | None]:
    # ex_dir: exercises/<construct>/<type>/<ex_slug>
    try:
        construct = ex_dir.parent.parent.name
        ex_type = ex_dir.parent.name
        return construct, ex_type
    except Exception:
        return None, None


def _check_teacher_files(ex_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    required = ["README.md", "OVERVIEW.md"]
    for filename in required:
        p = ex_dir / filename
        if not p.exists():
            findings.append(
                Finding(
                    "ERROR",
                    f"Missing teacher file: {p.relative_to(ex_dir)}",
                    path=p,
                )
            )

    return findings


def _check_order_of_teaching(ex_dir: Path, *, repo_root: Path, notebook_name: str) -> list[Finding]:
    findings: list[Finding] = []

    construct, _ex_type = _infer_construct_and_type(ex_dir)
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
    notebook_rel = f"notebooks/{notebook_name}"

    if slug not in text and notebook_rel not in text:
        findings.append(
            Finding(
                "ERROR",
                "OrderOfTeaching.md does not mention this exercise (add the exercise folder name or notebook path)",
                path=order_path,
            )
        )

    return findings


_EXERCISE_ID_RE = re.compile(r"^(ex\d{3})")


def _infer_exercise_id(slug: str) -> str | None:
    match = _EXERCISE_ID_RE.match(slug)
    if match is None:
        return None
    return match.group(1)


def _assign_binds_symbol(node: ast.Assign, symbol_name: str) -> bool:
    return any(
        isinstance(target, ast.Name) and target.id == symbol_name
        for target in node.targets
    )


def _ann_assign_binds_symbol(node: ast.AnnAssign, symbol_name: str) -> bool:
    return isinstance(node.target, ast.Name) and node.target.id == symbol_name


def _import_from_binds_symbol(node: ast.ImportFrom, symbol_name: str) -> bool:
    return any((alias.asname or alias.name) == symbol_name for alias in node.names)


def _node_binds_symbol(node: ast.stmt, symbol_name: str) -> bool:
    if isinstance(node, ast.Assign):
        return _assign_binds_symbol(node, symbol_name)
    if isinstance(node, ast.AnnAssign):
        return _ann_assign_binds_symbol(node, symbol_name)
    if isinstance(node, ast.ImportFrom):
        return _import_from_binds_symbol(node, symbol_name)
    return False


def _module_contains_symbol_binding(module: ast.Module, symbol_name: str) -> bool:
    return any(_node_binds_symbol(node, symbol_name) for node in module.body)


def _ast_contains_assigned_name(module_path: Path, symbol_name: str) -> bool:
    try:
        source_text = module_path.read_text(encoding="utf-8")
        module = ast.parse(source_text)
    except (FileNotFoundError, SyntaxError):
        return False
    return _module_contains_symbol_binding(module, symbol_name)


def _call_name(node: ast.Call) -> str | None:
    func_node = node.func
    if isinstance(func_node, ast.Name):
        return func_node.id
    if isinstance(func_node, ast.Attribute):
        return func_node.attr
    return None


def _is_name(node: ast.AST, value: str) -> bool:
    return isinstance(node, ast.Name) and node.id == value


def _checker_uses_modify_gate(checker_module_path: Path) -> bool:
    try:
        source_text = checker_module_path.read_text(encoding="utf-8")
        module = ast.parse(source_text)
    except (FileNotFoundError, SyntaxError):
        return False

    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node) != "check_modify_exercise_started":
            continue
        return True
    return False


def _checker_has_modify_gate_baseline_wiring(
    checker_module_path: Path,
    baseline_symbol: str,
) -> bool:
    try:
        source_text = checker_module_path.read_text(encoding="utf-8")
        module = ast.parse(source_text)
    except (FileNotFoundError, SyntaxError):
        return False

    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node) != "check_modify_exercise_started":
            continue
        if any(_is_name(arg, baseline_symbol) for arg in node.args):
            return True
        if any(_is_name(keyword.value, baseline_symbol) for keyword in node.keywords):
            return True
    return False


def _check_checker_module_exists(exercise_id: str, repo_root: Path) -> list[Finding]:
    checker_module_path = repo_root / "tests" / \
        "student_checker" / "checks" / f"{exercise_id}.py"
    if checker_module_path.exists():
        return []
    return [
        Finding(
            "ERROR",
            f"Missing student checker module: tests/student_checker/checks/{exercise_id}.py",
            path=checker_module_path,
        )
    ]


def _check_expectations_baseline_export(
    *,
    exercise_id: str,
    repo_root: Path,
    baseline_symbol: str,
) -> list[Finding]:
    expectations_dir = repo_root / "tests" / "exercise_expectations"
    expectation_candidates = sorted(
        expectations_dir.glob(f"{exercise_id}_*.py"))
    if not expectation_candidates:
        return [
            Finding(
                "ERROR",
                f"Missing expectations module matching tests/exercise_expectations/{exercise_id}_*.py",
                path=expectations_dir,
            )
        ]

    if any(_ast_contains_assigned_name(path, baseline_symbol) for path in expectation_candidates):
        return []

    return [
        Finding(
            "ERROR",
            f"No expectations module exports {baseline_symbol}",
            path=expectation_candidates[0],
        )
    ]


def _check_checker_modify_gate_wiring(
    *,
    checker_module_path: Path,
    baseline_symbol: str,
) -> list[Finding]:
    if _checker_has_modify_gate_baseline_wiring(checker_module_path, baseline_symbol):
        return []
    return [
        Finding(
            "ERROR",
            f"Checker wiring must call check_modify_exercise_started with {baseline_symbol}",
            path=checker_module_path,
        )
    ]


def _check_modify_gate_test_module_exists(exercise_id: str, repo_root: Path) -> list[Finding]:
    modify_gate_test_module_path = (
        repo_root / "tests" / "student_checker" /
        f"test_modify_gate_{exercise_id}.py"
    )
    if modify_gate_test_module_path.exists():
        return []
    return [
        Finding(
            "ERROR",
            f"Missing modify-gate test module: tests/student_checker/test_modify_gate_{exercise_id}.py",
            path=modify_gate_test_module_path,
        )
    ]


def _check_modify_gate_semantic_wiring(
    *,
    ex_slug: str,
    repo_root: Path,
    ex_type: str | None,
) -> list[Finding]:
    findings: list[Finding] = []
    exercise_id = _infer_exercise_id(ex_slug)
    if exercise_id is None:
        return findings

    baseline_symbol = f"{exercise_id.upper()}_MODIFY_STARTER_BASELINES"
    checker_module_path = repo_root / "tests" / \
        "student_checker" / "checks" / f"{exercise_id}.py"

    should_check = ex_type == "modify"
    if checker_module_path.exists() and _checker_uses_modify_gate(checker_module_path):
        should_check = True

    if not should_check:
        return findings

    findings.extend(_check_checker_module_exists(exercise_id, repo_root))
    findings.extend(
        _check_expectations_baseline_export(
            exercise_id=exercise_id,
            repo_root=repo_root,
            baseline_symbol=baseline_symbol,
        )
    )
    findings.extend(
        _check_checker_modify_gate_wiring(
            checker_module_path=checker_module_path,
            baseline_symbol=baseline_symbol,
        )
    )
    findings.extend(_check_modify_gate_test_module_exists(
        exercise_id, repo_root))

    return findings


def check_modify_gate_semantic_wiring(
    *,
    ex_slug: str,
    repo_root: Path,
    ex_type: str | None,
) -> list[Finding]:
    """Check semantic start-gate wiring for scaffolded exercises."""
    return _check_modify_gate_semantic_wiring(
        ex_slug=ex_slug,
        repo_root=repo_root,
        ex_type=ex_type,
    )


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
                "WARN",
                f"Exercise tags are not contiguous: found {exercise_nums}, expected {expected}",
                path=nb_path,
            )
        )

    if expect_debug and explanation_tags:
        exp_nums = _tag_numbers(explanation_tags, _EXPLANATION_TAG_RE)
        if exp_nums and max(exp_nums) < max(exercise_nums):
            findings.append(
                Finding(
                    "WARN",
                    "Some exercise parts may be missing matching explanationN cells",
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
            findings.append(
                Finding("ERROR", f"Cell {idx} is not an object", path=nb_path))
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

    # If we're in construct K, then constructs strictly after K are disallowed.
    disallowed = CONSTRUCT_ORDER[allowed_idx + 1:]

    for construct in disallowed:
        for pat in rules.get(construct, []):
            # Special-case: allow a single top-level `def solve()` wrapper (and returns inside it)
            if construct == "functions":
                func_defs = list(re.finditer(
                    r"^\s*def\s+([A-Za-z_]\w*)\s*\(", text, re.M))
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
                        e = func_defs[idx + 1].start() if idx + \
                            1 < len(func_defs) else len(text)
                        regions.append((s, e))
                    return_positions = [m.start()
                                        for m in re.finditer(r"\breturn\b", text)]
                    if return_positions and all(
                        any(s <= pos < e for s, e in regions) for pos in return_positions
                    ):
                        continue
                # otherwise fallthrough to regular warning

            if pat.search(text):
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
        code_chunks.append(_cell_source_text(cell))
    return "\n\n".join(code_chunks)


def _print_findings(findings: list[Finding]) -> None:
    for f in findings:
        loc = f" ({f.path})" if f.path else ""
        print(f"{f.severity}: {f.message}{loc}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "notebook",
        type=Path,
        help="Path to the student notebook under notebooks/",
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
        help="Construct to validate progression against (default: inferred from exercises/)",
    )
    parser.add_argument(
        "--type",
        choices=["debug", "modify", "make"],
        default=None,
        help="Exercise type (default: inferred from exercises/)",
    )

    args = parser.parse_args(argv)

    nb_path = args.notebook
    repo_root = args.repo_root

    slug = _infer_exercise_slug_from_notebook(nb_path)
    if slug is None:
        print("ERROR: Notebook path must end with .ipynb")
        return 2

    ex_dir = _find_exercise_dir(slug, repo_root)
    inferred_construct: str | None = None
    inferred_type: str | None = None
    if ex_dir is not None:
        inferred_construct, inferred_type = _infer_construct_and_type(ex_dir)

    construct = args.construct or inferred_construct
    ex_type = args.type or inferred_type

    findings: list[Finding] = []

    # Teacher files
    if ex_dir is None:
        findings.append(
            Finding(
                "WARN",
                f"Could not locate exercises/ directory for {slug!r} (skipping teacher-file checks)",
                path=repo_root / "exercises",
            )
        )
    else:
        findings.extend(_check_teacher_files(ex_dir))
        findings.extend(
            _check_order_of_teaching(
                ex_dir, repo_root=repo_root, notebook_name=nb_path.name)
        )

    findings.extend(
        check_modify_gate_semantic_wiring(
            ex_slug=slug,
            repo_root=repo_root,
            ex_type=ex_type,
        )
    )

    # Notebook structure (student)
    nb_student = _load_notebook(nb_path)
    expect_debug = ex_type == "debug"
    findings.extend(_check_notebook_structure(
        nb_path, nb_student, expect_debug=expect_debug))

    # Notebook structure (solutions mirror) if present
    nb_solution_path = repo_root / "notebooks" / "solutions" / nb_path.name
    if nb_solution_path.exists():
        nb_solution = _load_notebook(nb_solution_path)
        findings.extend(
            _check_notebook_structure(
                nb_solution_path, nb_solution, expect_debug=expect_debug)
        )
    else:
        findings.append(
            Finding("WARN", "Solution mirror notebook not found",
                    path=nb_solution_path)
        )

    # Progression scan (student + solution)
    if construct is None:
        findings.append(
            Finding(
                "WARN",
                "Could not infer construct; pass --construct to enable progression checks",
                path=nb_path,
            )
        )
    else:
        student_text = _collect_code_cell_text(nb_student)
        findings.extend(
            _scan_for_progression_violations(
                text=student_text, allowed_construct=construct, path=nb_path
            )
        )

        if nb_solution_path.exists():
            solution_text = _collect_code_cell_text(
                _load_notebook(nb_solution_path))
            findings.extend(
                _scan_for_progression_violations(
                    text=solution_text,
                    allowed_construct=construct,
                    path=nb_solution_path,
                )
            )

    # Report
    _print_findings(findings)

    error_count = sum(1 for f in findings if f.severity == "ERROR")
    warn_count = sum(1 for f in findings if f.severity == "WARN")

    if error_count:
        print(f"\nFAIL: {error_count} error(s), {warn_count} warning(s)")
        return 1

    print(f"\nOK: {warn_count} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
