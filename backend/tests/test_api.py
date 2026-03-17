from __future__ import annotations

import time


def test_api_training_and_simulation_flow(client) -> None:
    train_response = client.post("/api/v1/ai/train")
    assert train_response.status_code == 200
    assert train_response.json()["status"] == "training_completed"

    start_response = client.post(
        "/api/v1/simulation/start",
        json={
            "algorithm": "RSA",
            "attack_type": "power",
            "runs": 48,
            "enable_ai": True,
            "auto_defense": True,
        },
    )
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "simulation_started"

    time.sleep(0.15)

    status_response = client.get("/api/v1/simulation/status")
    assert status_response.status_code == 200
    assert status_response.json()["algorithm"] == "RSA"

    metrics_response = client.get("/api/v1/metrics/current")
    assert metrics_response.status_code == 200
    assert "execution_time_ms" in metrics_response.json()

    history_response = client.get("/api/v1/metrics/history?limit=5")
    assert history_response.status_code == 200
    assert isinstance(history_response.json(), list)

    attack_response = client.get("/api/v1/attack/status")
    assert attack_response.status_code == 200
    assert "best_key_guess" in attack_response.json()

    defense_response = client.get("/api/v1/defense/status")
    assert defense_response.status_code == 200
    assert "defense_mode" in defense_response.json()

    export_response = client.get("/api/v1/dataset/export")
    assert export_response.status_code == 200
    assert "text/csv" in export_response.headers["content-type"]


def test_websocket_metrics_stream(client) -> None:
    client.post(
        "/api/v1/simulation/start",
        json={
            "algorithm": "AES",
            "attack_type": "timing",
            "runs": 24,
            "enable_ai": True,
            "auto_defense": True,
        },
    )
    with client.websocket_connect("/api/v1/ws/metrics") as websocket:
        frame = websocket.receive_json()
        assert "simulation" in frame
        assert "current" in frame
