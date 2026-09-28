"""Contract tests for the Classroom 50 *test* harness helpers.

The three support modules behind the Classroom 50 grading tests -
``tests/_classroom50_lock.py``, ``tests/_classroom50_source_scan.py``, and
``tests/_classroom50_bootstrap.py`` - are test code, not production code, and
their own behaviour still has to be right: an AST helper that matches nothing, or
a marker evaluation that is always true, would make the Stage 3 red suite prove
less than it appears to.

These tests are therefore expected to be green.  They assert the documented
behaviour of the helpers, not the ``classroom50/result/v1`` or bootstrap
contracts, which live in ``tests/test_classroom50_native_autograder.py``,
``tests/test_classroom50_native_bootstrap.py``, and
``tests/test_classroom50_bundle_stage4.py``.
"""

from __future__ import annotations

import ast

import pytest

from tests._classroom50_bootstrap import is_manifest_records
from tests._classroom50_lock import (
    active_platform_pins,
    lock_derived_requirements,
    locked_active_pins,
    locked_closure_pins,
    locked_markers,
    requirement_markers,
    requirement_pins,
    windows_active,
)
from tests._classroom50_source_scan import (
    calls_named,
    code_string_literals,
    imports_pytest,
    non_deferred_pytest_imports,
    non_stdlib_module_imports,
    pytest_import_sites,
)

BOOTSTRAP_NAME = "bootstrap_native_dependencies"


def _statements(source: str) -> list[ast.stmt]:
    """Return the top-level statements of ``source`` for single-statement fixtures."""
    return ast.parse(source).body


def test_calls_named_matches_a_bare_call() -> None:
    """A direct ``name(...)`` call is matched."""
    statement = _statements(f"{BOOTSTRAP_NAME}()")[0]
    assert calls_named(statement, BOOTSTRAP_NAME) is True


def test_calls_named_matches_a_module_qualified_call() -> None:
    """A ``module.name(...)`` call is matched by its bare name too."""
    statement = _statements(f"helpers.{BOOTSTRAP_NAME}()")[0]
    assert calls_named(statement, BOOTSTRAP_NAME) is True
    nested = _statements(f"outer(inner.{BOOTSTRAP_NAME}())")[0]
    assert calls_named(nested, BOOTSTRAP_NAME) is True


@pytest.mark.parametrize(
    "source",
    [
        "other_callable()",
        f"{BOOTSTRAP_NAME}_helper()",
        f"other.{BOOTSTRAP_NAME}_helper()",
        "value = 1",
    ],
    ids=("other-name", "longer-name", "longer-module-qualified", "no-call"),
)
def test_calls_named_ignores_every_other_call(source: str) -> None:
    """A different callable never matches, including one that shares a prefix."""
    assert calls_named(_statements(source)[0], BOOTSTRAP_NAME) is False


def test_imports_pytest_recognises_both_import_forms() -> None:
    """``import pytest`` and ``from pytest import main`` are both runtime imports."""
    assert imports_pytest(_statements("import pytest")[0]) is True
    assert imports_pytest(_statements("from pytest import main")[0]) is True
    assert imports_pytest(_statements("import packaging")[0]) is False


def test_non_deferred_pytest_imports_separates_runtime_from_type_only_imports() -> None:
    """A function-body and a ``TYPE_CHECKING`` import are deferred; a module one is not."""
    source = (
        "import os\n"
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    import pytest\n"
        "def run() -> None:\n"
        "    import pytest\n"
    )
    assert non_deferred_pytest_imports(source) == []
    assert non_deferred_pytest_imports("import pytest\n") == ["import pytest"]


def test_pytest_import_sites_reports_only_functions_that_import_pytest() -> None:
    """The deferred-import sites are reported with their body statements."""
    source = "def run() -> None:\n    import pytest\n\n\ndef other() -> None:\n    pass\n"
    sites = pytest_import_sites(source)
    assert list(sites) == ["run"]
    assert [ast.unparse(step) for step in sites["run"]] == ["import pytest"]


def test_non_stdlib_module_imports_ignores_stdlib_and_type_only_imports() -> None:
    """Only runtime, non-stdlib imports run at module load are reported."""
    source = "import os\nimport packaging\nfrom typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import pytest\n"
    assert non_stdlib_module_imports(source) == {"packaging": ["import packaging"]}


def test_code_string_literals_excludes_docstrings() -> None:
    """Prose in a docstring can neither satisfy nor break a literal scan."""
    source = '"""Docstring mentioning uv."""\nNAME = "uv"\n'
    assert code_string_literals(source) == ["uv"]


def test_the_lock_derivation_and_the_requirements_parsing_agree() -> None:
    """The rendered fixture parses back to the locked pins and markers."""
    text = lock_derived_requirements()
    assert requirement_pins(text) == locked_closure_pins()
    assert requirement_markers(text) == locked_markers()
    assert active_platform_pins(text) == locked_active_pins()


def test_the_active_platform_subset_follows_the_marker() -> None:
    """``colorama`` is in the active set exactly on the platform its marker selects."""
    active = active_platform_pins(lock_derived_requirements())
    assert ("colorama" in active) is windows_active()


def test_is_manifest_records_rejects_a_non_list_and_a_non_object_entry() -> None:
    """The manifest guard accepts only a list whose every entry is a JSON object."""
    assert is_manifest_records([{"exercise_key": "ex001"}]) is True
    assert is_manifest_records([]) is True
    assert is_manifest_records({"exercise_key": "ex001"}) is False
    assert is_manifest_records(["ex001"]) is False
