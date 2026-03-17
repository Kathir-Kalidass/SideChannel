#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
SENDER_PID_FILE="$RUN_DIR/sender.pid"
RECEIVER_PID_FILE="$RUN_DIR/receiver.pid"
ATTACKER_PID_FILE="$RUN_DIR/attacker.pid"

stop_pid_file() {
  local pid_file="$1"
  local name="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name PID file not found"
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $name (PID $pid)"
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      echo "Force stopping $name (PID $pid)"
      kill -9 "$pid" 2>/dev/null || true
    fi
  else
    echo "$name process already stopped"
  fi
  rm -f "$pid_file"
}

stop_pid_file "$BACKEND_PID_FILE" "Backend"
stop_pid_file "$FRONTEND_PID_FILE" "Frontend"
stop_pid_file "$SENDER_PID_FILE" "Sender channel"
stop_pid_file "$RECEIVER_PID_FILE" "Receiver channel"
stop_pid_file "$ATTACKER_PID_FILE" "Attacker channel"

echo "Stopping PostgreSQL"
(cd "$ROOT_DIR" && docker compose stop postgres)

echo "Stack stopped"
