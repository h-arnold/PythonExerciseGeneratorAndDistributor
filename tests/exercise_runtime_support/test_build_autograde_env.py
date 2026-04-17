"""Regression tests for autograde environment helper contracts."""

from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path

import exercise_runtime_support.helpers
from exercise_runtime_support.execution_variant import ACTIVE_VARIANT_ENV_VAR
from exercise_runtime_support.helpers import build_autograde_env

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOVED_HELPER_NAMES = [
    "resolve_notebook_path",
    "run_tagged_cell_output",
    "load_notebook",
    "assert_code_cell_present",
    "get_explanation_cell",
]


def test_build_autograde_env_sets_pythonpath_to_repo_root_when_absent() -> None:
    env = build_autograde_env(base_env={})

    assert env["PYTHONPATH"] == str(REPO_ROOT)


def test_build_autograde_env_with_empty_base_env_does_not_inherit_process_vars(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AUTOGRADE_SENTINEL", "present-in-process")

    env = build_autograde_env(base_env={})

    assert "AUTOGRADE_SENTINEL" not in env


def test_build_autograde_env_prepends_repo_root_to_existing_pythonpath() -> None:
    env = build_autograde_env(base_env={"PYTHONPATH": "existing:path"})

    assert env["PYTHONPATH"] == f"{REPO_ROOT}{os.pathsep}existing:path"


def test_build_autograde_env_defaults_plugin_autoload_and_student_variant() -> None:
    env = build_autograde_env(base_env={})

    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert env[ACTIVE_VARIANT_ENV_VAR] == "student"


def test_build_autograde_env_preserves_existing_plugin_autoload_value() -> None:
    env = build_autograde_env(base_env={"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "0"})

    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "0"


def test_build_autograde_env_overrides_replace_values_and_remove_keys() -> None:
    env = build_autograde_env(
        base_env={
            "KEEP_ME": "original",
            "REMOVE_ME": "present",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "0",
        },
        overrides={
            "KEEP_ME": "updated",
            "REMOVE_ME": None,
            ACTIVE_VARIANT_ENV_VAR: "solution",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": None,
        },
    )

    assert env["KEEP_ME"] == "updated"
    assert env[ACTIVE_VARIANT_ENV_VAR] == "solution"
    assert "REMOVE_ME" not in env
    assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" not in env


def test_helpers_module_exports_only_build_autograde_env() -> None:
    assert exercise_runtime_support.helpers.__all__ == ["build_autograde_env"]
    assert hasattr(exercise_runtime_support.helpers, "build_autograde_env")
    assert not hasattr(exercise_runtime_support.helpers, "REPO_ROOT")
    assert not hasattr(
        exercise_runtime_support.helpers,
        "configure_variant_environment",
    )


def test_tests_helpers_exports_only_build_autograde_env() -> None:
    runtime_helpers_module = import_module("exercise_runtime_support.helpers")
    helpers_module = import_module("tests.helpers")

    shim_public = {
        name
        for name in vars(helpers_module)
        if not name.startswith("_") and not name.startswith("__")
    }

    assert runtime_helpers_module.__all__ == ["build_autograde_env"]
    assert helpers_module.__all__ == ["build_autograde_env"]
    assert shim_public == {"build_autograde_env"}
    assert runtime_helpers_module.build_autograde_env is build_autograde_env
    assert helpers_module.build_autograde_env is build_autograde_env
    assert not hasattr(runtime_helpers_module, "REPO_ROOT")
    assert not hasattr(runtime_helpers_module, "configure_variant_environment")

    for removed_name in REMOVED_HELPER_NAMES:
        assert not hasattr(runtime_helpers_module, removed_name)
        assert not hasattr(helpers_module, removed_name)
