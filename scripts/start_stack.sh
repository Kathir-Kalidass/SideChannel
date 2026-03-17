#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
SENDER_PID_FILE="$RUN_DIR/sender.pid"
RECEIVER_PID_FILE="$RUN_DIR/receiver.pid"
ATTACKER_PID_FILE="$RUN_DIR/attacker.pid"

mkdir -p "$RUN_DIR"

wait_for_url() {
  local url="$1"
  local name="$2"
  local timeout_s="${3:-45}"
  local start_ts
  start_ts="$(date +%s)"

  while true; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name is ready at $url"
      return 0
    fi

    if (( $(date +%s) - start_ts > timeout_s )); then
      echo "Timed out waiting for $name at $url"
      return 1
    fi
    sleep 1
  done
}

if [[ ! -f "$ROOT_DIR/.env" && -f "$ROOT_DIR/.env.example" ]]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "Created .env from .env.example"
fi

if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
  echo "Setting up backend environment"
  "$ROOT_DIR/scripts/setup_backend.sh"
fi

PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

start_channel() {
  local role="$1"
  local port="$2"
  local pid_file="$3"
  local log_file="$RUN_DIR/${role}.log"

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$role channel already running with PID $(cat "$pid_file")"
    return
  fi

  echo "Starting $role channel on port $port"
  nohup "$PYTHON_BIN" "$ROOT_DIR/scripts/channel_node.py" --role "$role" --port "$port" >"$log_file" 2>&1 &
  echo $! >"$pid_file"
}

if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
  echo "Installing frontend dependencies"
  (cd "$ROOT_DIR/frontend" && npm install)
fi

echo "Starting PostgreSQL"
(cd "$ROOT_DIR" && docker compose up -d postgres)

if [[ -f "$BACKEND_PID_FILE" ]] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
  echo "Backend already running with PID $(cat "$BACKEND_PID_FILE")"
else
  echo "Starting backend"
  nohup "$ROOT_DIR/scripts/run_backend.sh" >"$RUN_DIR/backend.log" 2>&1 &
  echo $! >"$BACKEND_PID_FILE"
fi

if [[ -f "$FRONTEND_PID_FILE" ]] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
  echo "Frontend already running with PID $(cat "$FRONTEND_PID_FILE")"
else
  echo "Starting frontend"
  nohup "$ROOT_DIR/scripts/run_frontend.sh" >"$RUN_DIR/frontend.log" 2>&1 &
  echo $! >"$FRONTEND_PID_FILE"
fi

wait_for_url "http://localhost:8000/api/v1/simulation/status" "Backend API" 60
wait_for_url "http://localhost:5173" "Frontend" 60

start_channel "sender" "7101" "$SENDER_PID_FILE"
start_channel "receiver" "7102" "$RECEIVER_PID_FILE"
start_channel "attacker" "7103" "$ATTACKER_PID_FILE"

wait_for_url "http://localhost:7101/health" "Sender channel" 30
wait_for_url "http://localhost:7102/health" "Receiver channel" 30
wait_for_url "http://localhost:7103/health" "Attacker channel" 30

echo "Stack started"
echo "Backend log: $RUN_DIR/backend.log"
echo "Frontend log: $RUN_DIR/frontend.log"
echo "Sender log: $RUN_DIR/sender.log"
echo "Receiver log: $RUN_DIR/receiver.log"
echo "Attacker log: $RUN_DIR/attacker.log"
