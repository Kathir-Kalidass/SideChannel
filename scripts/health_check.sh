#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing .venv interpreter at $PYTHON_BIN"
  exit 1
fi

export HEALTH_API_BASE="${HEALTH_API_BASE:-http://localhost:8000/api/v1}"
export HEALTH_FRONTEND_BASE="${HEALTH_FRONTEND_BASE:-http://localhost:5173}"
export HEALTH_WS_URL="${HEALTH_WS_URL:-ws://localhost:8000/api/v1/ws/metrics}"
export HEALTH_SENDER_URL="${HEALTH_SENDER_URL:-http://localhost:7101/health}"
export HEALTH_RECEIVER_URL="${HEALTH_RECEIVER_URL:-http://localhost:7102/health}"
export HEALTH_ATTACKER_URL="${HEALTH_ATTACKER_URL:-http://localhost:7103/health}"

"$PYTHON_BIN" - <<'PY'
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request

import websockets

API = os.environ["HEALTH_API_BASE"].rstrip("/")
FRONTEND = os.environ["HEALTH_FRONTEND_BASE"].rstrip("/")
WS_URL = os.environ["HEALTH_WS_URL"]
SENDER_URL = os.environ["HEALTH_SENDER_URL"]
RECEIVER_URL = os.environ["HEALTH_RECEIVER_URL"]
ATTACKER_URL = os.environ["HEALTH_ATTACKER_URL"]


def http_request(method, path, body=None, expected=(200,)):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(f"{API}{path}", method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            payload = resp.read()
            text = payload.decode("utf-8") if payload else ""
            parsed = json.loads(text) if text else None
            if status not in expected:
                raise RuntimeError(f"{method} {path} returned {status}, expected {expected}")
            return parsed
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}") from exc


def frontend_check():
    req = urllib.request.Request(FRONTEND, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.getcode() != 200:
            raise RuntimeError(f"Frontend unavailable: HTTP {resp.getcode()}")


def channel_check(url, name):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.getcode() != 200:
            raise RuntimeError(f"{name} unavailable: HTTP {resp.getcode()}")


async def ws_check():
    async with websockets.connect(WS_URL, open_timeout=10, close_timeout=5) as ws:
        raw = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise RuntimeError("WebSocket payload is not an object")
        if "simulation" not in data:
            raise RuntimeError("WebSocket payload missing simulation field")


def wait_for_metrics(max_attempts=10):
    for _ in range(max_attempts):
        current = http_request("GET", "/metrics/current")
        if current and isinstance(current, dict) and current.get("algorithm"):
            return current
        import time

        time.sleep(1)
    raise RuntimeError("Metrics did not become available after simulation start")


def run_algorithm_checks():
    algorithms = ["AES", "ChaCha20", "RSA", "ECC"]
    for algorithm in algorithms:
        print(f"Checking algorithm simulation: {algorithm}")
        started = http_request(
            "POST",
            "/simulation/start",
            {
                "algorithm": algorithm,
                "attack_type": "power",
                "runs": 20,
                "enable_ai": True,
                "auto_defense": True,
            },
        )
        if started.get("status") != "simulation_started":
            raise RuntimeError(f"Simulation did not start for {algorithm}")

        current = wait_for_metrics()
        if current.get("algorithm") != algorithm:
            raise RuntimeError(
                f"Metrics algorithm mismatch: expected {algorithm}, got {current.get('algorithm')}"
            )

        stopped = http_request("POST", "/simulation/stop")
        if stopped.get("status") != "simulation_stopped":
            raise RuntimeError(f"Simulation did not stop cleanly for {algorithm}")


def run_checks():
    print("Checking frontend availability")
    frontend_check()

    print("Checking channel ports")
    channel_check(SENDER_URL, "Sender channel")
    channel_check(RECEIVER_URL, "Receiver channel")
    channel_check(ATTACKER_URL, "Attacker channel")

    print("Checking core REST endpoints")
    status = http_request("GET", "/simulation/status")
    if "status" not in status:
        raise RuntimeError("/simulation/status missing status field")

    _ = http_request("GET", "/metrics/history?limit=5")
    _ = http_request("GET", "/attack/status")
    _ = http_request("GET", "/attack/log")
    _ = http_request("GET", "/ai/prediction")
    _ = http_request("GET", "/defense/status")

    print("Checking payment user endpoints")
    users = http_request("GET", "/payments/users")
    if not isinstance(users, list) or len(users) == 0:
        raise RuntimeError("/payments/users returned no users")
    login_result = http_request("POST", "/payments/login", {"username": "alice.pay", "password": "alice123"})
    if "user" not in login_result:
        raise RuntimeError("/payments/login response missing user")
    adaptive = http_request("GET", "/payments/adaptive-policy?sender_user_id=1&receiver_user_id=2")
    if "thresholds" not in adaptive:
        raise RuntimeError("/payments/adaptive-policy response missing thresholds")
    _ = http_request("GET", "/payments/history?limit=5")

    print("Checking AI training endpoint")
    train = http_request("POST", "/ai/train")
    if "accuracy" not in train:
        raise RuntimeError("/ai/train response missing accuracy")

    print("Checking defense activation and disable")
    activate = http_request("POST", "/defense/activate", {"technique": "masking"})
    if activate.get("status") != "defense_activated":
        raise RuntimeError("Defense activation failed")
    disable = http_request("POST", "/defense/disable")
    if disable.get("status") != "defense_disabled":
        raise RuntimeError("Defense disable failed")

    print("Checking dataset export endpoint")
    req = urllib.request.Request(f"{API}/dataset/export", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.getcode() != 200:
            raise RuntimeError(f"dataset/export failed with HTTP {resp.getcode()}")
        content = resp.read(1024)
        if not content:
            raise RuntimeError("dataset/export returned empty payload")

    run_algorithm_checks()

    print("Checking WebSocket stream")
    asyncio.run(ws_check())


if __name__ == "__main__":
    try:
        run_checks()
    except Exception as exc:
        print(f"Health check failed: {exc}")
        sys.exit(1)
    print("Health check passed")
PY
