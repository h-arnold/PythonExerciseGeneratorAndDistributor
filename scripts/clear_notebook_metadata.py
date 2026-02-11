"""Utility to clear notebook metadata before commits."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Sequence
from pathlib import Path

DEFAULT_SCAN_PATHS = ("notebooks",)


def iter_notebook_paths(paths: Iterable[Path]) -> set[Path]:
    """Return a set of tracked notebook paths under the given start paths."""
    resolved: list[Path] = []
    for path in paths:
        if path.is_dir():
            resolved.extend(path.rglob("*.ipynb"))
        elif path.is_file() and path.suffix == ".ipynb":
            resolved.append(path)
    return {p for p in resolved if p.exists()}


def clear_notebook_metadata(path: Path) -> bool:
    """Ensure the notebook has empty metadata, returning True if a rewrite occurred."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    metadata = notebook.get("metadata")
    if metadata == {}:
        return False
    notebook["metadata"] = {}
    path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description="Clear notebook metadata.")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=list(DEFAULT_SCAN_PATHS),
        help="Paths or directories to scan for *.ipynb files.",
    )
    args = parser.parse_args(argv)

    inputs = [Path(p) for p in args.paths]
    notebooks = iter_notebook_paths(inputs)
    updated: list[Path] = []
    for notebook in sorted(notebooks):
        if clear_notebook_metadata(notebook):
            updated.append(notebook)
    if updated:
        print("Cleared metadata in:", ", ".join(str(p) for p in updated))
        print("Please stage the updated notebooks before committing.")
        return 1
    return 0


def entry_point() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entry_point()
