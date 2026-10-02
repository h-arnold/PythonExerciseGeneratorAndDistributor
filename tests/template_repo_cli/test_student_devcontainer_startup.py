"""Tests for the student devcontainer startup surface.

The student template delegates ``postStartCommand`` to
``.devcontainer/post_start.sh``, which syncs dependencies and launches the Jupyter
kernel watchdog in a detached background process. These tests pin the wiring, the
packaged copy, and the script's shell behaviour (warn-and-continue, detached
launch, retained diagnostics) without ever starting a real watchdog.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import time
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts import jupyter_watchdog

DEVCONTAINER_DIR = Path("template_repo_files") / ".devcontainer"
POST_START_SCRIPT = "post_start.sh"

# Stub `uv`: records every invocation, reports a configurable `uv sync` status,
# and either fails the `uv run` launch or behaves like the watchdog by writing a
# start banner and then blocking on a FIFO so the launched process can be
# inspected after post_start.sh has already exited.
STUB_UV = """#!/usr/bin/env bash
printf '%s\\n' "$*" >>"${STUB_UV_CALLS_FILE}"
case "$1" in
    sync)
        printf '%s\\n' 'stub uv sync output'
        exit "${STUB_UV_SYNC_STATUS:-0}"
        ;;
    run)
        shift
        if [ -n "${STUB_UV_RUN_ERROR:-}" ]; then
            printf '%s\\n' "${STUB_UV_RUN_ERROR}" >&2
            exit "${STUB_UV_RUN_STATUS:-1}"
        fi
        printf 'pid=%s sid=%s\\n' "$$" "$(ps -o sid= -p "$$" | tr -d ' ')" \
            >"${STUB_UV_PROCESS_FILE}"
        printf '%s\\n' "${STUB_UV_BANNER}" >>"${STUB_UV_WATCHDOG_LOG_FILE}"
        exec 3<"${STUB_UV_KEEPALIVE_FIFO}"
        read -r _ <&3
        exit 0
        ;;
esac
exit 0
"""

_POST_START_COMMAND_RE = re.compile(r'"postStartCommand"\s*:\s*"((?:\\.|[^"\\])*)"')
_BANNER_RE = re.compile(r'^watchdog_banner="(?P<banner>[^"]+)"', re.MULTILINE)
_TERMINATE_ATTEMPTS = 20


def _post_start_command(repo_root: Path) -> str:
    """Read ``postStartCommand`` from the student devcontainer.json (JSONC with comments)."""
    raw = (repo_root / DEVCONTAINER_DIR / "devcontainer.json").read_text(encoding="utf-8")
    match = _POST_START_COMMAND_RE.search(raw)
    assert match is not None, "student devcontainer.json has no postStartCommand"
    return str(json.loads(f'"{match.group(1)}"'))


def _post_start_source(repo_root: Path) -> str:
    """Return the startup script source shipped in the student template."""
    return (repo_root / DEVCONTAINER_DIR / POST_START_SCRIPT).read_text(encoding="utf-8")


def _banner_in_post_start(repo_root: Path) -> str:
    """Return the start banner the startup script waits for."""
    match = _BANNER_RE.search(_post_start_source(repo_root))
    assert match is not None, "post_start.sh must define the watchdog start banner"
    return str(match.group("banner"))


@dataclass
class StartupHarness:
    """One throwaway student workspace driven by ``post_start.sh`` with a stub ``uv``."""

    workspace: Path
    state_home: Path
    banner: str
    calls_file: Path
    process_file: Path
    keepalive: Path
    env: dict[str, str]
    sync_status: int = 0
    run_error: str = ""
    run_status: int = 1

    @property
    def startup_log(self) -> Path:
        """Startup script log, expected under the XDG state directory."""
        return self.state_home / "python-tutor" / "post_start.log"

    @property
    def watchdog_log(self) -> Path:
        """Watchdog log, expected under the XDG state directory."""
        return self.state_home / "python-tutor" / "jupyter_watchdog.log"

    def run(self) -> subprocess.CompletedProcess[str]:
        """Run the startup script from outside the workspace, as the container would."""
        env = dict(self.env)
        env["STUB_UV_SYNC_STATUS"] = str(self.sync_status)
        env["STUB_UV_RUN_ERROR"] = self.run_error
        env["STUB_UV_RUN_STATUS"] = str(self.run_status)
        env["STUB_UV_BANNER"] = self.banner
        script = self.workspace / DEVCONTAINER_DIR.name / POST_START_SCRIPT
        return subprocess.run(
            ["bash", str(script)],
            cwd=self.workspace.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def uv_calls(self) -> list[str]:
        """Return every ``uv`` invocation the script made."""
        if not self.calls_file.exists():
            return []
        return self.calls_file.read_text(encoding="utf-8").splitlines()

    def launched_process(self) -> dict[str, int]:
        """Return the ``pid``/``sid`` the stub recorded for the launched process."""
        recorded = dict(
            field.split("=") for field in self.process_file.read_text(encoding="utf-8").split()
        )
        return {"pid": int(recorded["pid"]), "sid": int(recorded["sid"])}

    def release_launched_process(self) -> None:
        """Unblock the launched stub so no process outlives the test."""
        try:
            fd = os.open(self.keepalive, os.O_WRONLY | os.O_NONBLOCK)
        except OSError:
            return
        try:
            os.write(fd, b"\n")
        except OSError:
            pass
        finally:
            os.close(fd)


def _is_running(pid: int) -> bool:
    """Return whether a pid still exists (a blocked stub process counts as running)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@pytest.fixture
def startup(repo_root: Path, tmp_path: Path) -> Generator[StartupHarness]:
    """Build a student workspace whose ``uv`` is a recording stub."""
    workspace = tmp_path / "workspace"
    (workspace / "scripts").mkdir(parents=True)
    (workspace / DEVCONTAINER_DIR.name).mkdir()
    (workspace / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (workspace / "scripts" / "jupyter_watchdog.py").write_text("# stub\n", encoding="utf-8")
    shutil.copy2(
        repo_root / DEVCONTAINER_DIR / POST_START_SCRIPT,
        workspace / DEVCONTAINER_DIR.name / POST_START_SCRIPT,
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub_uv = bin_dir / "uv"
    stub_uv.write_text(STUB_UV, encoding="utf-8")
    stub_uv.chmod(0o755)

    keepalive = tmp_path / "keepalive.fifo"
    os.mkfifo(keepalive)

    state_home = tmp_path / "state"
    calls_file = tmp_path / "uv_calls.txt"
    process_file = tmp_path / "uv_process.txt"
    harness = StartupHarness(
        workspace=workspace,
        state_home=state_home,
        banner=_banner_in_post_start(repo_root),
        calls_file=calls_file,
        process_file=process_file,
        keepalive=keepalive,
        env={
            "HOME": str(tmp_path / "home"),
            "XDG_STATE_HOME": str(state_home),
            "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
            "STUB_UV_CALLS_FILE": str(calls_file),
            "STUB_UV_PROCESS_FILE": str(process_file),
            "STUB_UV_WATCHDOG_LOG_FILE": str(state_home / "python-tutor" / "jupyter_watchdog.log"),
            "STUB_UV_KEEPALIVE_FIFO": str(keepalive),
        },
    )

    yield harness
    harness.release_launched_process()
    _terminate_launched_process(harness)


def _signal_pid(pid: int, sig: signal.Signals) -> None:
    """Signal a pid, tolerating one that exited between the check and the signal."""
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, sig)


def _terminate_launched_process(harness: StartupHarness) -> None:
    """Best-effort teardown of the detached stub process."""
    try:
        pid = harness.launched_process()["pid"]
    except (FileNotFoundError, KeyError, ValueError):
        return
    for _ in range(_TERMINATE_ATTEMPTS):
        _signal_pid(pid, signal.SIGTERM)
        if not _is_running(pid):
            return
        time.sleep(0.05)
    _signal_pid(pid, signal.SIGKILL)


class TestStudentDevcontainerWiring:
    """The packaged devcontainer must delegate startup to the script via bash."""

    def test_post_start_command_runs_script_with_bash(self, repo_root: Path) -> None:
        """The script is invoked through ``bash`` so no executable bit is required."""
        assert _post_start_command(repo_root).split() == [
            "bash",
            f".devcontainer/{POST_START_SCRIPT}",
        ]

    def test_post_start_script_banner_matches_watchdog(self, repo_root: Path) -> None:
        """Startup confirmation greps for the banner the watchdog actually logs."""
        assert _banner_in_post_start(repo_root) == jupyter_watchdog.START_BANNER


@pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("setsid") is None,
    reason="post_start.sh needs bash and setsid",
)
class TestPostStartScriptBehaviour:
    """Shell-level behaviour of the startup script, driven by a stub ``uv``."""

    def test_missing_pyproject_warns_and_exits_zero(self, startup: StartupHarness) -> None:
        """Without a pyproject.toml the script warns, skips uv, and never fails."""
        (startup.workspace / "pyproject.toml").unlink()

        result = startup.run()

        assert result.returncode == 0
        assert "Warning: no pyproject.toml" in result.stdout
        assert startup.uv_calls() == []

    def test_sync_failure_warns_and_still_launches_watchdog(self, startup: StartupHarness) -> None:
        """A failed ``uv sync`` is warned about but must not block the lesson."""
        startup.sync_status = 1

        result = startup.run()

        assert result.returncode == 0
        assert "'uv sync' failed" in result.stdout
        assert startup.uv_calls() == ["sync", "run --no-sync scripts/jupyter_watchdog.py"]
        assert "Jupyter watchdog started" in result.stdout

    def test_watchdog_launch_failure_is_recorded(self, startup: StartupHarness) -> None:
        """A dead launch is reported and its diagnostics are kept outside the workspace."""
        startup.run_error = "error: No virtual environment found"

        result = startup.run()

        assert result.returncode == 0
        assert "could not confirm the Jupyter watchdog started" in result.stdout
        assert startup.run_error in startup.watchdog_log.read_text(encoding="utf-8")

    def test_watchdog_launch_is_detached_and_outlives_the_script(
        self, startup: StartupHarness
    ) -> None:
        """``setsid`` gives the watchdog its own session, so it survives postStart exit."""
        result = startup.run()

        assert result.returncode == 0
        assert (
            startup.watchdog_log.read_text(encoding="utf-8").count(jupyter_watchdog.START_BANNER)
            == 1
        )

        launched = startup.launched_process()
        assert _is_running(launched["pid"])
        assert launched["sid"] == launched["pid"]
        assert launched["sid"] != os.getsid(0)

    def test_logs_are_written_outside_the_workspace(self, startup: StartupHarness) -> None:
        """Startup output goes to the XDG state dir, never into the student workspace."""
        startup.sync_status = 1

        startup.run()

        startup_log = startup.startup_log
        assert startup_log.is_relative_to(startup.state_home)
        assert ".devcontainer" not in startup_log.parts
        assert "stub uv sync output" in startup_log.read_text(encoding="utf-8")
        assert not list(startup.workspace.glob("**/*.log"))
