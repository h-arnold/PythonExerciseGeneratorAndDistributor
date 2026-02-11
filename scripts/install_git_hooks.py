"""Set up the repository to load hooks from .githooks."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    """Point git's hooksPath at the repo-local .githooks directory."""
    repo_root = Path(__file__).resolve().parents[1]
    hooks_dir = repo_root / ".githooks"
    hooks_dir.mkdir(exist_ok=True)

    target = str(hooks_dir.relative_to(repo_root))
    try:
        subprocess.run(["git", "config", "core.hooksPath", target], check=True)
    except subprocess.CalledProcessError as exc:
        print("Failed to set core.hooksPath", exc)
        return exc.returncode or 1

    print(f"Configured git hooks from {hooks_dir}")
    return 0


def entry_point() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entry_point()
