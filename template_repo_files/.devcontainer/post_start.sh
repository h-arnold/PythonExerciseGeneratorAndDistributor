#!/usr/bin/env bash
#
# Devcontainer postStart startup for the student template.
#
# Invoked as `bash .devcontainer/post_start.sh` from devcontainer.json so the
# packaged template never depends on an executable bit surviving a Git checkout.
#
# Contract: this script must never block the lesson. Every problem is warned
# about on the devcontainer output pane and appended to
# ${XDG_STATE_HOME:-~/.local/state}/python-tutor/post_start.log, then startup
# continues.
#
#   1. Run `uv sync`, warning (but not failing) when it fails.
#   2. Launch scripts/jupyter_watchdog.py in a detached background process.
#   3. Confirm the watchdog actually started rather than trusting a backgrounded
#      launch, so a false success always leaves a trace.
#
# Logs live outside .devcontainer/ so they never pollute the student workspace:
#   post_start.log        this script's own output plus the `uv sync` output
#   jupyter_watchdog.log  the watchdog's own log

set -u

workspace_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "${workspace_dir}" || exit 0

state_dir="${XDG_STATE_HOME:-${HOME}/.local/state}/python-tutor"
startup_log="${state_dir}/post_start.log"
watchdog_log="${state_dir}/jupyter_watchdog.log"
watchdog_script="scripts/jupyter_watchdog.py"
# Must match START_BANNER in scripts/jupyter_watchdog.py.
watchdog_banner="Jupyter kernel watchdog started"
watchdog_confirm_attempts=40
watchdog_confirm_interval=0.1

mkdir -p -- "${state_dir}"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "${startup_log}"
}

# postCreateCommand installs uv with `pip install --user`, which lands outside the
# image's default PATH, so make sure uv stays reachable in this lifecycle step.
export PATH="${HOME}/.local/bin:${PATH}"

if [ ! -f pyproject.toml ]; then
    log "Warning: no pyproject.toml in ${workspace_dir}; skipping 'uv sync' and the watchdog."
    exit 0
fi

log "Running 'uv sync' in ${workspace_dir}."
if ! uv sync >>"${startup_log}" 2>&1; then
    log "Warning: 'uv sync' failed (see ${startup_log}). Continuing so the lesson can still start."
fi

if [ ! -f "${watchdog_script}" ]; then
    log "Warning: ${watchdog_script} is missing; the Jupyter watchdog will not run."
    exit 0
fi

# The watchdog log survives container restarts, so only look for the banner in
# the bytes this launch writes; otherwise a stale banner would confirm a failed
# launch.
watchdog_log_offset=0
if [ -f "${watchdog_log}" ]; then
    watchdog_log_offset="$(wc -c <"${watchdog_log}")"
fi

# `setsid` puts the watchdog in its own session, so it outlives this postStart
# shell and any SIGHUP aimed at that shell's process group. stdin is detached
# from the (absent) terminal and both streams are captured in the watchdog log,
# so an immediate startup failure stays inspectable instead of going to /dev/null.
# `--no-sync` keeps the launch from repeating the sync that just ran above.
log "Launching the Jupyter kernel watchdog..."
setsid uv run --no-sync "${watchdog_script}" >>"${watchdog_log}" 2>&1 </dev/null &
watchdog_pid=$!

# A backgrounded launch looks successful the instant the shell forks, which is
# how a watchdog that dies immediately used to be indistinguishable from a
# healthy one. Wait for the watchdog's own start banner instead, giving up as
# soon as the launched process is gone. Give it one polling interval after the
# banner to catch a launcher that prints the banner and immediately exits.
watchdog_confirmed=0
for ((attempt = 1; attempt <= watchdog_confirm_attempts; attempt++)); do
    if tail -c "+$((watchdog_log_offset + 1))" -- "${watchdog_log}" 2>/dev/null \
        | grep -qF "${watchdog_banner}"; then
        sleep "${watchdog_confirm_interval}"
        if kill -0 "${watchdog_pid}" 2>/dev/null; then
            watchdog_confirmed=1
        fi
        break
    fi
    if ! kill -0 "${watchdog_pid}" 2>/dev/null; then
        break
    fi
    sleep "${watchdog_confirm_interval}"
done

if [ "${watchdog_confirmed}" -eq 1 ]; then
    log "Jupyter watchdog started (launcher pid ${watchdog_pid}); log: ${watchdog_log}"
else
    log "Warning: could not confirm the Jupyter watchdog started (launcher pid ${watchdog_pid}); see ${watchdog_log}"
fi

exit 0
