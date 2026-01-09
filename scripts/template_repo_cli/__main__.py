"""Allow running the CLI as a module: python -m scripts.template_repo_cli"""

from scripts.template_repo_cli.cli import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
