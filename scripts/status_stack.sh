#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
SENDER_PID_FILE="$RUN_DIR/sender.pid"
RECEIVER_PID_FILE="$RUN_DIR/receiver.pid"
ATTACKER_PID_FILE="$RUN_DIR/attacker.pid"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"
SENDER_LOG="$RUN_DIR/sender.log"
RECEIVER_LOG="$RUN_DIR/receiver.log"
ATTACKER_LOG="$RUN_DIR/attacker.log"

BACKEND_URL="${BACKEND_URL:-http://localhost:8000/api/v1/simulation/status}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
SENDER_URL="${SENDER_URL:-http://localhost:7101/health}"
RECEIVER_URL="${RECEIVER_URL:-http://localhost:7102/health}"
ATTACKER_URL="${ATTACKER_URL:-http://localhost:7103/health}"

print_header() {
  echo
  echo "========== $1 =========="
}

pid_status() {
  local pid_file="$1"
  local name="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name: NOT RUNNING (pid file missing)"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    local cmd
    cmd="$(ps -p "$pid" -o comm= 2>/dev/null | xargs || true)"
    echo "$name: RUNNING (pid=$pid, cmd=${cmd:-unknown})"
  else
    echo "$name: NOT RUNNING (stale pid file pid=$pid)"
  fi
}

http_status() {
  local name="$1"
  local url="$2"

  local code
  code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
  if [[ "$code" == "200" ]]; then
    echo "$name URL: UP ($url)"
  else
    echo "$name URL: DOWN ($url, http=$code)"
  fi
}

port_status() {
  local port="$1"
  local label="$2"

  local lines
  lines="$(ss -ltnp 2>/dev/null | awk -v p=":$port" '$4 ~ p {print}')"
  if [[ -n "$lines" ]]; then
    echo "$label port $port: LISTENING"
    echo "$lines"
  else
    echo "$label port $port: NOT LISTENING"
  fi
}

docker_status() {
  if command -v docker >/dev/null 2>&1; then
    local cid
    cid="$(cd "$ROOT_DIR" && docker compose ps -q postgres 2>/dev/null || true)"
    if [[ -n "$cid" ]]; then
      local state
      state="$(docker inspect -f '{{.State.Status}}' "$cid" 2>/dev/null || true)"
      echo "PostgreSQL container: ${state:-unknown}"
    else
      echo "PostgreSQL container: NOT FOUND"
    fi
  else
    echo "Docker: not installed"
  fi
}

tail_log() {
  local file="$1"
  local name="$2"

  if [[ -f "$file" ]]; then
    echo "Last 20 lines: $file"
    tail -n 20 "$file"
  else
    echo "$name log not found: $file"
  fi
}

print_header "Stack Process Status"
pid_status "$BACKEND_PID_FILE" "Backend"
pid_status "$FRONTEND_PID_FILE" "Frontend"
pid_status "$SENDER_PID_FILE" "Sender channel"
pid_status "$RECEIVER_PID_FILE" "Receiver channel"
pid_status "$ATTACKER_PID_FILE" "Attacker channel"

print_header "Service Reachability"
http_status "Backend API" "$BACKEND_URL"
http_status "Frontend" "$FRONTEND_URL"
http_status "Sender channel" "$SENDER_URL"
http_status "Receiver channel" "$RECEIVER_URL"
http_status "Attacker channel" "$ATTACKER_URL"

print_header "Port Status"
port_status 8000 "Backend"
port_status 5173 "Frontend"
port_status 5433 "PostgreSQL"
port_status 7101 "Sender channel"
port_status 7102 "Receiver channel"
port_status 7103 "Attacker channel"

print_header "Database Container"
docker_status

print_header "Backend Logs"
tail_log "$BACKEND_LOG" "Backend"

print_header "Frontend Logs"
tail_log "$FRONTEND_LOG" "Frontend"

print_header "Channel Logs"
tail_log "$SENDER_LOG" "Sender"
tail_log "$RECEIVER_LOG" "Receiver"
tail_log "$ATTACKER_LOG" "Attacker"
