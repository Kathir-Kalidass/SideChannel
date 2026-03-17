#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$ROOT_DIR/backend/requirements.txt"

echo "Backend environment ready: $PYTHON_BIN"
