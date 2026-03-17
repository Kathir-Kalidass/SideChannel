from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

TEST_DB_PATH = ROOT / "data" / "test-side-channel.db"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB_PATH}"
os.environ["MODEL_PATH"] = str(ROOT / "data" / "test-attack-model.joblib")
os.environ["SYNTHETIC_DATASET_SIZE"] = "320"
os.environ["SIMULATION_TICK_SECONDS"] = "0.02"
os.environ["SIMULATION_BATCH_SIZE"] = "12"

from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
