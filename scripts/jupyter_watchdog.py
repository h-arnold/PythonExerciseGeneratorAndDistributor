#!/usr/bin/env python3
"""Jupyter kernel healthcheck watchdog for VS Code devcontainers.

VS Code's Jupyter extension in Linux devcontainers uses "raw kernel" mode:
each notebook has a direct ipykernel_launcher process with ZeroMQ sockets
(hb, control, shell, stdin, iopub) and a runtime JSON file at
~/.local/share/jupyter/runtime/kernel-*.json. There is no Jupyter server.

This watchdog:
  1. Discovers kernels by scanning the runtime directory for kernel-*.json
     files that have a corresponding ipykernel_launcher process.
  2. Each interval, sends a ZeroMQ heartbeat ping to the kernel's hb_port.
  3. If a kernel fails to respond, kills the ipykernel_launcher process so
     VS Code detects the dead kernel and prompts/auto-restarts it.

Logs to .devcontainer/jupyter_watchdog.log.
"""

from __future__ import annotations

import glob
import json
import os
import signal
import subprocess
import sys
import time

import zmq

# Configuration
WATCHDOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(WATCHDOG_DIR, ".devcontainer", "jupyter_watchdog.log")
RUNTIME_DIR = os.path.expanduser("~/.local/share/jupyter/runtime")
INTERVAL_SECONDS = 30
HEARTBEAT_TIMEOUT_MS = 5000
SHUTDOWN_GRACE_SECONDS = 3


def log(msg: str) -> None:
    """Append a timestamped message to the log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {msg}\n")


def find_kernel_process(runtime_file: str) -> str | None:
    """Return the PID of the ipykernel_launcher process for a runtime file."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    for line in result.stdout.splitlines():
        if "ipykernel_launcher" not in line:
            continue
        if runtime_file in line:
            return line.split(None, 1)[0].strip()
    return None


def discover_kernels() -> list[dict[str, str]]:
    """Discover active kernels by scanning the Jupyter runtime directory."""
    if not os.path.isdir(RUNTIME_DIR):
        return []
    kernels: list[dict[str, str]] = []
    for runtime_file in sorted(glob.glob(os.path.join(RUNTIME_DIR, "kernel-*.json"))):
        try:
            with open(runtime_file, encoding="utf-8") as fh:
                info = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            log(f"  ! Could not read {runtime_file}: {exc}")
            continue
        pid = find_kernel_process(runtime_file)
        if pid is None:
            continue
        kernels.append(
            {
                "file": runtime_file,
                "pid": pid,
                "hb_port": str(info.get("hb_port", "")),
                "shell_port": str(info.get("shell_port", "")),
            }
        )
    return kernels


def heartbeat_alive(hb_port: str, timeout_ms: int) -> bool:
    """Send a ZeroMQ heartbeat ping. Returns True if the kernel responds."""
    if not hb_port:
        return False
    ctx = zmq.Context.instance()
    sock = ctx.socket(zmq.REQ)
    sock.setsockopt(zmq.LINGER, 0)
    sock.setsockopt(zmq.RCVTIMEO, timeout_ms)
    sock.setsockopt(zmq.SNDTIMEO, timeout_ms)
    try:
        sock.connect(f"tcp://127.0.0.1:{hb_port}")
        sock.send(b"ping")
        return sock.recv() == b"ping"
    except zmq.error.Again:
        return False
    except zmq.error.ZMQError:
        return False
    finally:
        sock.close(0)


def _send_signal(pid_int: int, sig: signal.Signals, action: str) -> bool:
    """Send a signal to a process. Returns True if the signal was sent, False otherwise."""
    try:
        os.kill(pid_int, sig)
        log(f"  -> {action} to PID {pid_int}")
        return True
    except ProcessLookupError:
        log(f"  -> PID {pid_int} already gone")
        return False
    except PermissionError:
        log(f"  ! Permission denied {action.lower()} to PID {pid_int}")
        return False


def _wait_for_exit(pid_int: int) -> bool:
    """Wait for a process to exit. Returns True if exited, False on timeout."""
    deadline = time.monotonic() + SHUTDOWN_GRACE_SECONDS
    while time.monotonic() < deadline:
        try:
            os.kill(pid_int, 0)
        except ProcessLookupError:
            log(f"  -> PID {pid_int} exited cleanly")
            return True
        except PermissionError:
            log(f"  ! Permission denied checking status of PID {pid_int}")
            return True
        time.sleep(0.2)
    return False


def kill_kernel(pid: str, runtime_file: str) -> None:
    """Terminate a kernel process, escalating to SIGKILL if it ignores SIGTERM."""
    try:
        pid_int = int(pid)
    except ValueError:
        log(f"  ! Invalid PID: {pid}")
        return

    if not _send_signal(pid_int, signal.SIGTERM, "Sent SIGTERM"):
        return

    if _wait_for_exit(pid_int):
        return

    _send_signal(pid_int, signal.SIGKILL, "Sent SIGKILL")


def main() -> int:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log("=" * 60)
    log("Jupyter kernel watchdog started")
    log(f"  Interval:        {INTERVAL_SECONDS}s")
    log(f"  Runtime dir:     {RUNTIME_DIR}")
    log(f"  Heartbeat time:  {HEARTBEAT_TIMEOUT_MS}ms")
    log(f"  Log file:        {LOG_FILE}")
    log("=" * 60)

    stopped = False

    def _handle_signal(signum: int, _frame: object) -> None:
        nonlocal stopped
        log(f"Received signal {signum}, stopping watchdog.")
        stopped = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    iteration = 0
    while not stopped:
        iteration += 1
        kernels = discover_kernels()
        if not kernels:
            log(
                f"[iter {iteration}] No active kernels found "
                f"(open a notebook in VS Code to start one)"
            )
            time.sleep(INTERVAL_SECONDS)
            continue

        log(f"[iter {iteration}] Found {len(kernels)} active kernel(s)")
        for kernel in kernels:
            short_file = os.path.basename(kernel["file"])
            if heartbeat_alive(kernel["hb_port"], HEARTBEAT_TIMEOUT_MS):
                log(f"  OK   PID {kernel['pid']:<6}  port {kernel['hb_port']:<5}  {short_file}")
                continue
            log(f"  DEAD PID {kernel['pid']:<6}  port {kernel['hb_port']:<5}  {short_file}")
            kill_kernel(kernel["pid"], kernel["file"])

        time.sleep(INTERVAL_SECONDS)

    log("Watchdog stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
