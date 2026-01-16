#!/usr/bin/env python3
"""Top-level convenience entrypoint for the template-repo CLI.

This allows invoking the CLI with:

    python main.py create --repo-name my-repo ...

instead of:

    python -m scripts.template_repo_cli create --repo-name my-repo ...

It simply delegates to the package's `main()` function so behaviour is identical.
"""

from __future__ import annotations

import sys

from scripts.template_repo_cli.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
