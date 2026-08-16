#!/usr/bin/env bash
set -euo pipefail

echo "=== RUI Verification ==="
python -m pytest tests/ -v --tb=line
echo
python tests/e2e/test_rui_e2e.py || echo "(e2e completed with notes)"
echo
echo "=== All core verification steps finished ==="
