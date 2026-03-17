#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing .venv. Run scripts/setup_backend.sh first."
  exit 1
fi

if [[ -f "$ROOT_DIR/.env" ]]; then
  echo "Using env file at $ROOT_DIR/.env"
else
  echo "No .env file found, using default backend settings."
fi

exec "$PYTHON_BIN" -m uvicorn app.main:app --app-dir "$ROOT_DIR/backend" --host 0.0.0.0 --port 8000 --reload
