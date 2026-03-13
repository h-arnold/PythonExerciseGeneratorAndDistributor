#!/usr/bin/env bash
set -euo pipefail

# Run the full pytest suite against the mirrored solution notebooks.
# Usage:
#   scripts/verify_solutions.sh
#   scripts/verify_solutions.sh -q
#   scripts/verify_solutions.sh tests/test_ex003_sequence_modify_variables.py

python scripts/run_pytest_variant.py --variant solution "$@"
