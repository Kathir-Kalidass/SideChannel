#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"

post_json() {
  local path="$1"
  local payload="$2"
  curl -fsS -X POST "$API_BASE$path" -H "Content-Type: application/json" -d "$payload"
}

get_json() {
  local path="$1"
  curl -fsS "$API_BASE$path"
}

algorithms=("AES" "ChaCha20" "RSA" "ECC")

for algorithm in "${algorithms[@]}"; do
  echo "Running simulation for $algorithm"
  post_json "/simulation/start" "{\"algorithm\":\"$algorithm\",\"attack_type\":\"power\",\"runs\":50,\"enable_ai\":true,\"auto_defense\":true}" >/dev/null

  sleep 2
  metrics="$(get_json "/metrics/current")"
  echo "Current metrics for $algorithm:"
  echo "$metrics"

  post_json "/simulation/stop" "{}" >/dev/null
  echo "Completed simulation for $algorithm"
  echo "---"
  sleep 1
done

echo "All algorithm simulations completed"
