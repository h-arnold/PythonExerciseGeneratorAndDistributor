"""Tests for the Jupyter kernel watchdog log location.

The watchdog log deliberately lives outside the repository (and therefore outside
``.devcontainer/``) so it never appears in a student workspace. These tests pin
that location plus the start banner the devcontainer startup script waits for to
confirm the watchdog actually launched.
"""

from __future__ import annotations

import importlib
import signal
from collections.abc import Generator
from pathlib import Path

import pytest

from scripts import jupyter_watchdog


class _StopLoop(Exception):
    """Raised in place of kernel discovery to end ``main()`` after its startup log."""


def _raise_stop_loop() -> list[dict[str, str]]:
    """Abort the watchdog loop immediately, after its startup banner is written."""
    raise _StopLoop


@pytest.fixture(autouse=True)
def _restore_watchdog_module() -> Generator[None]:
    """Reload the module after each test so patched paths never leak between tests."""
    yield
    importlib.reload(jupyter_watchdog)


def test_log_file_lives_in_xdg_state_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``XDG_STATE_HOME`` decides where the watchdog log is written."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    importlib.reload(jupyter_watchdog)

    expected = tmp_path / "state" / "python-tutor" / "jupyter_watchdog.log"
    assert expected == jupyter_watchdog.LOG_FILE


def test_log_file_defaults_to_local_state_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Without ``XDG_STATE_HOME`` the log falls back to ``~/.local/state``."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setenv("HOME", str(home))

    importlib.reload(jupyter_watchdog)

    expected = home / ".local" / "state" / "python-tutor" / "jupyter_watchdog.log"
    assert expected == jupyter_watchdog.LOG_FILE


def test_log_file_is_outside_the_devcontainer_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The log path must not sit in a ``.devcontainer`` folder or the repository."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    importlib.reload(jupyter_watchdog)

    assert ".devcontainer" not in jupyter_watchdog.LOG_FILE.parts


def test_log_appends_timestamped_lines(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``log()`` appends one timestamped line per call to the configured log file."""
    log_file = tmp_path / "logs" / "jupyter_watchdog.log"
    log_file.parent.mkdir()
    monkeypatch.setattr(jupyter_watchdog, "LOG_FILE", log_file)

    jupyter_watchdog.log(jupyter_watchdog.START_BANNER)

    written = log_file.read_text(encoding="utf-8")
    assert written.count("\n") == 1
    assert written.endswith(f"{jupyter_watchdog.START_BANNER}\n")


def test_main_logs_start_banner_before_iterating(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The banner is logged at startup, which is what startup confirmation greps for."""
    log_file = tmp_path / "jupyter_watchdog.log"
    monkeypatch.setattr(jupyter_watchdog, "LOG_FILE", log_file)
    monkeypatch.setattr(jupyter_watchdog, "discover_kernels", _raise_stop_loop)
    previous_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}

    try:
        with pytest.raises(_StopLoop):
            jupyter_watchdog.main()
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert jupyter_watchdog.START_BANNER in lines[1]
