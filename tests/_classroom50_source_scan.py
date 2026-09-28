"""AST source analysis for the Stage 3 Classroom 50 native contract.

``ACTION_PLAN.md`` Stage 3 requires the bundle-local grader to import pytest only
after the fresh target has been installed and verified, and to run before that
target exists at all.  Both are structural rules about ``scripts/autograder.py``'s
*source*, so they are checked by parsing it rather than by running it: this module
answers "where is each import executed", "which installed packages does this
module reach for", and "does this statement call that callable".

It also holds the vocabulary those scans enforce - the modules the bundle or the
student checkout owns, the one installed package a deferred import may reach, the
dependency manifests a native run must never read, and the ``uv`` executables it
must never run.  The lock-derived requirements data lives in
``tests/_classroom50_lock.py`` and the seam contract itself in
``tests/_classroom50_bootstrap.py``.
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Mapping
from typing import Final

from tests._classroom50_test_helpers import REPO_ROOT

# The autograder may import the modules the bundle and the student checkout own:
# they are not installed packages, so reading them proves nothing about the
# environment the native install is meant to isolate.
BUNDLE_OWNED_IMPORTS: Final[frozenset[str]] = frozenset(
    {"classroom50_manifest", "exercise_metadata", "exercise_runtime_support"}
)
# The one installed package the autograder may import, and only inside a function
# body, after the fresh target has been verified.
DEFERRED_THIRD_PARTY_IMPORTS: Final[frozenset[str]] = frozenset({"pytest"})

# Dependency manifests a native run must never read: the bundle requirements file
# is the only install source, so the student checkout cannot influence it.
STUDENT_DEPENDENCY_MANIFESTS: Final[tuple[str, ...]] = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "uv.lock",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "environment.yml",
    "constraints.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
)
UV_EXECUTABLES: Final[tuple[str, ...]] = ("uv", "uv.exe", "uvx", "uvx.exe")


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Return the ids of every module, class, and function docstring literal.

    The literal itself is collected, not its owner: filtering on the owner node
    would leave the docstring in the result and make prose about the contract
    indistinguishable from a name the code actually uses.
    """
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        first = node.body[0] if node.body else None
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            docstrings.add(id(first.value))
    return docstrings


def code_string_literals(source: str) -> list[str]:
    """Return every string constant in ``source`` except docstrings.

    Docstrings are excluded so prose about the contract can neither satisfy nor
    break an assertion about what the code actually reads or executes.
    """
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    """Return a child-to-parent map for every node in ``tree``."""
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _ancestors(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> list[ast.AST]:
    """Return every enclosing scope of ``node``, innermost first."""
    ancestors: list[ast.AST] = []
    current: ast.AST | None = node
    while current in parents:
        current = parents[current]
        ancestors.append(current)
    return ancestors


def _is_type_checking_guard(node: ast.AST) -> bool:
    """Return True when ``node`` is an ``if TYPE_CHECKING:`` type-checking guard."""
    return isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test)


def _is_type_checking_guarded(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> bool:
    """Return True when ``node`` sits inside an ``if TYPE_CHECKING:`` guard."""
    return any(_is_type_checking_guard(ancestor) for ancestor in _ancestors(node, parents))


def imported_module_names(statement: ast.AST) -> set[str]:
    """Return the top-level module names ``statement`` imports."""
    names: set[str] = set()
    for node in ast.walk(statement):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def imports_pytest(statement: ast.stmt) -> bool:
    """Return True when ``statement`` performs a runtime ``import pytest``."""
    return any(
        (isinstance(node, ast.Import) and any(alias.name == "pytest" for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "pytest")
        for node in ast.walk(statement)
    )


def calls_named(statement: ast.stmt, name: str) -> bool:
    """Return True when ``statement`` calls ``name``, bare or module-qualified.

    Only the final attribute is compared, so a module-qualified call such as
    ``helpers.bootstrap_native_dependencies(...)`` matches the bare name: the seam
    contract is about which callable runs, not about how it is reached.  A name
    that merely shares a prefix never matches, and neither does a call to a
    differently named callable.
    """
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name | ast.Attribute)
        and ast.unparse(node.func).rsplit(".", maxsplit=1)[-1] == name
        for node in ast.walk(statement)
    )


def non_deferred_pytest_imports(source: str) -> list[str]:
    """Return every pytest import that is not deferred into a function body.

    ``SPEC.md`` requires that "``pytest`` must not be imported at module load; the
    import is deferred until after the fresh target has been installed".  A
    ``TYPE_CHECKING``-guarded import never executes at runtime, so it counts as
    deferred rather than as a module-scope import.
    """
    tree = ast.parse(source)
    parents = _parents(tree)
    not_deferred: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import | ast.ImportFrom) or not imports_pytest(node):
            continue
        ancestors = _ancestors(node, parents)
        inside_function = any(
            isinstance(ancestor, ast.FunctionDef | ast.AsyncFunctionDef) for ancestor in ancestors
        )
        if not (inside_function or _is_type_checking_guarded(node, parents)):
            not_deferred.append(ast.unparse(node))
    return not_deferred


def pytest_import_sites(source: str) -> dict[str, list[ast.stmt]]:
    """Return each function that imports pytest at runtime, with its body statements."""
    tree = ast.parse(source)
    return {
        node.name: node.body
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and any(imports_pytest(statement) for statement in node.body)
    }


def _enclosing_function(
    node: ast.AST, parents: Mapping[ast.AST, ast.AST]
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Return the innermost function enclosing ``node``, if any."""
    for ancestor in _ancestors(node, parents):
        if isinstance(ancestor, ast.FunctionDef | ast.AsyncFunctionDef):
            return ancestor
    return None


def _in_scope(node: ast.AST, parents: Mapping[ast.AST, ast.AST], owner: str | None) -> bool:
    """Return True when an import belongs to the requested module or function scope."""
    enclosing = _enclosing_function(node, parents)
    if owner is None:
        return enclosing is None
    return enclosing is not None and enclosing.name == owner


def _non_stdlib_imports(
    source: str, owner: str | None
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Return runtime and ``TYPE_CHECKING``-only non-stdlib imports for one scope.

    Args:
        source: Python source to inspect.
        owner: ``None`` for module-level imports, or a function name to inspect only
            that function's own body.
    """
    tree = ast.parse(source)
    parents = _parents(tree)
    found: dict[tuple[bool, str], list[str]] = {}
    if owner is not None:
        assert any(
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == owner
            for node in ast.walk(tree)
        ), f"scripts/autograder.py has no function named {owner!r}"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import | ast.ImportFrom) or not _in_scope(node, parents, owner):
            continue
        type_only = _is_type_checking_guarded(node, parents)
        for name in imported_module_names(node) - sys.stdlib_module_names:
            found.setdefault((type_only, name), []).append(ast.unparse(node))
    runtime = {name: lines for (type_only, name), lines in found.items() if not type_only}
    return runtime, {name: lines for (type_only, name), lines in found.items() if type_only}


def non_stdlib_module_imports(source: str) -> dict[str, list[str]]:
    """Return every non-stdlib import that runs while the module is imported.

    The autograder runs before the verified target exists, so a module-scope import
    of ``packaging`` (or any other installed package) would read the student's or
    the global environment instead of the bundle.
    """
    runtime, _ = _non_stdlib_imports(source, None)
    return runtime


def non_stdlib_imports_in_function(source: str, name: str) -> dict[str, list[str]]:
    """Return every non-stdlib import inside the function ``name``."""
    runtime, _ = _non_stdlib_imports(source, name)
    return runtime


def non_stdlib_imports_in_functions(source: str) -> dict[str, list[str]]:
    """Return every non-stdlib import executed inside any function of ``source``.

    A helper the bootstrap calls could otherwise import an installed package
    without appearing in the bootstrap function's own body, so the whole
    function-level surface is scanned as well.
    """
    tree = ast.parse(source)
    found: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for name, lines in non_stdlib_imports_in_function(source, node.name).items():
            found.setdefault(name, []).extend(lines)
    return found


def third_party_runtime_imports() -> set[str]:
    """Return every non-stdlib, non-bundle top-level module the runtime imports.

    The native requirement closure exists so the bundle's ``exercise_runtime_support``
    copy imports cleanly, so a runtime import that the closure misses is a
    requirements-source defect rather than a test artefact.
    """
    runtime_source = REPO_ROOT / "exercise_runtime_support"
    own_packages = ("exercise_metadata", "exercise_runtime_support")
    imported: set[str] = set()
    for path in sorted(runtime_source.rglob("*.py")):
        imported.update(imported_module_names(ast.parse(path.read_text(encoding="utf-8"))))
    return {
        name
        for name in imported
        if name not in sys.stdlib_module_names and name not in own_packages
    }
