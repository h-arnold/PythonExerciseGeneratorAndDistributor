# Jupyter Kernel Watchdog

Location: `scripts/jupyter_watchdog.py`

A userspace kernel health monitor for VS Code devcontainers that use Jupyter's raw kernel mode. It runs as a background `nohup` process launched by both devcontainer `postStartCommand` entries in this repository.

> **⚠️ Important:** The watchdog kills unresponsive kernels. It does **not** restart them. VS Code's built-in kernel recovery detects the death and either prompts the user or auto-restarts depending on user settings.

## Problem

VS Code's Jupyter extension in Linux devcontainers uses "raw kernel" mode: each notebook gets a direct `ipykernel_launcher` process with ZeroMQ sockets (hb, control, shell, stdin, iopub) and a runtime descriptor at `~/.local/share/jupyter/runtime/kernel-*.json`. There is no central Jupyter server, so when a kernel crashes silently or becomes wedged, nothing detects it automatically. The user is left with a "connecting..." indicator that never resolves.

## How it works

The watchdog runs a loop every 30 seconds:

1. **Discovery**: scans `~/.local/share/jupyter/runtime/kernel-*.json` for files that have a matching `ipykernel_launcher` process (confirmed via `ps`).
2. **Heartbeat**: opens a ZeroMQ `REQ` socket to each kernel's `hb_port` and sends a `b"ping"` message. Expects `b"pong"` within 5 seconds.
3. **Kill**: if a kernel does not respond, sends `SIGTERM` to the process. Waits 3 seconds (`SHUTDOWN_GRACE_SECONDS`). If the process has not exited, escalates to `SIGKILL`.
4. **Recovery**: VS Code detects the dead kernel and triggers its built-in restart or reconnection flow.

## Configuration

All tunables are module-level constants at the top of the script:

| Constant | Default | Description |
|---|---|---|
| `INTERVAL_SECONDS` | `30` | Polling interval between discovery-and-ping rounds |
| `HEARTBEAT_TIMEOUT_MS` | `5000` | ZeroMQ receive/send timeout in milliseconds. A kernel that doesn't respond within this window is considered dead. |
| `SHUTDOWN_GRACE_SECONDS` | `3` | Grace period after `SIGTERM` before escalating to `SIGKILL` |

## Invocation

The watchdog is launched as a background process from both devcontainer configurations:

**Maintainer devcontainer** (`/.devcontainer/devcontainer.json`):

```json
"postStartCommand": "nohup uv run scripts/jupyter_watchdog.py > /dev/null 2>&1 &"
```

**Student template devcontainer** (`/template_repo_files/.devcontainer/devcontainer.json`):

```json
"postStartCommand": "nohup uv run scripts/jupyter_watchdog.py > /dev/null 2>&1 &"
```

The student variant chains the watchdog with the environment sync command using `&&`; the maintainer variant runs it standalone.

> **💡 Tip:** To run the watchdog manually during development: `uv run python scripts/jupyter_watchdog.py`

## Logging

Logs are written to `.devcontainer/jupyter_watchdog.log` (relative to the repository root). Each line is timestamped and includes the iteration number where relevant.

Example log output:

```
[2026-07-09 10:15:00] ============================================================
[2026-07-09 10:15:00] Jupyter kernel watchdog started
[2026-07-09 10:15:00]   Interval:        30s
[2026-07-09 10:15:00]   Runtime dir:     /home/vscode/.local/share/jupyter/runtime
[2026-07-09 10:15:00]   Heartbeat time:  5000ms
[2026-07-09 10:15:00]   Log file:        /workspaces/PythonExerciseGeneratorAndDistributor/.devcontainer/jupyter_watchdog.log
[2026-07-09 10:15:00] ============================================================
[2026-07-09 10:15:30] [iter 1] No active kernels found (open a notebook in VS Code to start one)
[2026-07-09 10:16:00] [iter 2] Found 1 active kernel(s)
[2026-07-09 10:16:00]   OK   PID 1847    port 42615  kernel-7f8d3a2e.json
[2026-07-09 10:16:30] [iter 3] Found 0 active kernel(s)
[2026-07-09 10:17:00] [iter 4] Found 2 active kernel(s)
[2026-07-09 10:17:00]   OK   PID 1847    port 42615  kernel-7f8d3a2e.json
[2026-07-09 10:17:01]   DEAD PID 2019    port 42987  kernel-a1b2c3d4.json
[2026-07-09 10:17:01]   -> Sent SIGTERM to PID 2019
[2026-07-09 10:17:04]   -> Sent SIGKILL to PID 2019
```

- `OK` — kernel responded to heartbeat
- `DEAD` — kernel did not respond; kill sequence beginning
- `Sent SIGTERM` / `Sent SIGKILL` — signal actions taken
- `PID already gone` — process exited between discovery and kill attempt (race, handled gracefully)
- `Could not read ...` — a runtime JSON file was unreadable (permissions, partial write); skipped

## Shutdown

The watchdog registers handlers for `SIGTERM` and `SIGINT`. On receipt it sets a stop flag, the main loop exits on the next iteration boundary, and a shutdown message is logged. The devcontainer runtime sends `SIGTERM` when the container stops, so the watchdog exits cleanly without orphaned children.

## Dependencies

- **pyzmq** (`zmq`): ZeroMQ bindings for heartbeat communication. Declared in `pyproject.toml` and installed via `uv sync`. The script imports it at the top level, so a missing `zmq` will fail immediately on import — this is intentional (fail-fast).

## Troubleshooting

### Watchdog not running

Check for the process:

```bash
ps aux | grep jupyter_watchdog
```

If missing, start it manually: `uv run python scripts/jupyter_watchdog.py` and check the log.

### Log file growing large

The watchdog appends one line per kernel per 30s interval plus discovery rounds. With 1–3 active kernels, expect roughly 2 lines per minute. If log size is a concern, add log rotation or truncate it: `> .devcontainer/jupyter_watchdog.log`.

### "No active kernels found" on every iteration

Normal when no notebook is open in VS Code. Open or create a `.ipynb` file to start a kernel.

### Kernel keeps getting killed (repeated "DEAD" entries)

- Check whether the kernel process is genuinely crashing (look for OOM or segfault in system logs).
- Increase `HEARTBEAT_TIMEOUT_MS` if the kernel is slow to respond under load.
- Check for port conflicts or firewall rules blocking localhost ZeroMQ traffic.

## Related docs

- [Docker and DevContainer Setup](docker-devcontainer-setup.md) — how the watchdog is configured in both devcontainer variants
- [Project Structure](project-structure.md) — repository layout referencing this script
