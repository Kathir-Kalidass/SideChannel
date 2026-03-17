from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


class Settings(BaseSettings):
    app_name: str = "Intelligent Side-Channel Leakage Detection and Defense Simulator"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/side_channel"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    synthetic_dataset_size: int = 2400
    model_path: Path = DATA_DIR / "attack_model.joblib"
    simulation_tick_seconds: float = 1.0
    simulation_batch_size: int = 40
    auto_train_on_startup: bool = True
    ai_retrain_on_simulation_start: bool = True

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
