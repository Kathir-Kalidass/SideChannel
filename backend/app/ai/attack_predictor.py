from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.utils.helpers import risk_level


NUMERIC_FEATURES = [
    "execution_time_ms",
    "timing_variance",
    "cpu_usage_pct",
    "memory_usage_mb",
    "clock_cycles",
    "power_avg",
    "power_peak",
    "power_variance",
    "hamming_weight_mean",
    "hamming_distance_mean",
    "cache_hits",
    "cache_misses",
    "cache_miss_rate",
    "correlation_score",
    "leakage_score",
]
CATEGORICAL_FEATURES = ["algorithm", "attack_type", "defense_mode", "source"]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _random_secure_row(rng: np.random.Generator, algorithm: str, attack_type: str) -> dict[str, Any]:
    execution_time = rng.uniform(1.2, 8.5)
    timing_variance = rng.uniform(0.01, 0.06)
    power_avg = rng.uniform(18, 29)
    power_peak = power_avg + rng.uniform(2, 7)
    power_variance = rng.uniform(3.5, 11.5)
    cache_misses = int(rng.integers(2, 12))
    cache_hits = int(rng.integers(240, 330))
    miss_rate = round((cache_misses / (cache_hits + cache_misses)) * 100, 3)
    correlation_score = rng.uniform(0.08, 0.38)
    leakage_score = rng.uniform(0.12, 0.48)
    return {
        "algorithm": algorithm,
        "attack_type": attack_type,
        "execution_time_ms": round(execution_time, 4),
        "timing_variance": round(timing_variance, 4),
        "cpu_usage_pct": round(rng.uniform(12, 34), 4),
        "memory_usage_mb": round(rng.uniform(18, 48), 4),
        "clock_cycles": int(execution_time * 3200 + rng.integers(40, 220)),
        "power_avg": round(power_avg, 4),
        "power_peak": round(power_peak, 4),
        "power_variance": round(power_variance, 4),
        "hamming_weight_mean": round(rng.uniform(4.5, 9.8), 4),
        "hamming_distance_mean": round(rng.uniform(3.8, 9.2), 4),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_miss_rate": miss_rate,
        "correlation_score": round(correlation_score, 4),
        "leakage_score": round(leakage_score, 4),
        "defense_mode": rng.choice([True, False], p=[0.7, 0.3]),
        "label": "secure",
        "source": "synthetic",
    }


def _random_leakage_row(rng: np.random.Generator, algorithm: str, attack_type: str) -> dict[str, Any]:
    execution_time = rng.uniform(1.8, 9.4)
    timing_variance = rng.uniform(0.08, 0.24)
    power_avg = rng.uniform(26, 42)
    power_peak = power_avg + rng.uniform(6, 15)
    power_variance = rng.uniform(12, 34)
    cache_misses = int(rng.integers(10, 30))
    cache_hits = int(rng.integers(190, 290))
    miss_rate = round((cache_misses / (cache_hits + cache_misses)) * 100, 3)
    correlation_score = rng.uniform(0.58, 0.96)
    leakage_score = rng.uniform(0.62, 0.98)
    return {
        "algorithm": algorithm,
        "attack_type": attack_type,
        "execution_time_ms": round(execution_time, 4),
        "timing_variance": round(timing_variance, 4),
        "cpu_usage_pct": round(rng.uniform(26, 68), 4),
        "memory_usage_mb": round(rng.uniform(28, 78), 4),
        "clock_cycles": int(execution_time * 3300 + rng.integers(120, 480)),
        "power_avg": round(power_avg, 4),
        "power_peak": round(power_peak, 4),
        "power_variance": round(power_variance, 4),
        "hamming_weight_mean": round(rng.uniform(9.6, 16.4), 4),
        "hamming_distance_mean": round(rng.uniform(8.2, 14.8), 4),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_miss_rate": miss_rate,
        "correlation_score": round(correlation_score, 4),
        "leakage_score": round(leakage_score, 4),
        "defense_mode": rng.choice([True, False], p=[0.2, 0.8]),
        "label": "leakage",
        "source": "synthetic",
    }


def generate_synthetic_dataset(size: int) -> pd.DataFrame:
    rng = np.random.default_rng(27)
    algorithms = ["AES", "ChaCha20", "RSA", "ECC"]
    attack_types = ["power", "timing", "cache"]
    rows: list[dict[str, Any]] = []

    for _ in range(size):
        algorithm = algorithms[int(rng.integers(0, len(algorithms)))]
        attack_type = attack_types[int(rng.integers(0, len(attack_types)))]
        if rng.random() < 0.52:
            rows.append(_random_leakage_row(rng, algorithm, attack_type))
        else:
            rows.append(_random_secure_row(rng, algorithm, attack_type))

    return pd.DataFrame(rows)


class AttackPredictor:
    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.pipeline: Pipeline | None = None
        self.training_accuracy: float | None = None
        self.top_features: list[dict[str, float | str]] = []

    def ensure_model(self, dataset_size: int) -> None:
        if self.model_path.exists():
            payload = joblib.load(self.model_path)
            self.pipeline = payload["pipeline"]
            self.training_accuracy = payload["accuracy"]
            self.top_features = payload["top_features"]
            return
        self.train(generate_synthetic_dataset(dataset_size))

    def train(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        preprocessor = ColumnTransformer(
            transformers=[
                ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
                ("numeric", "passthrough", NUMERIC_FEATURES),
            ]
        )
        model = RandomForestClassifier(
            n_estimators=180,
            max_depth=10,
            min_samples_split=4,
            random_state=27,
        )
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", model),
            ]
        )

        X = dataframe[MODEL_FEATURES]
        y = dataframe["label"]
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=27,
            stratify=y,
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        accuracy = round(float(accuracy_score(y_test, predictions)), 4)

        feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
        importances = pipeline.named_steps["model"].feature_importances_
        ranked = sorted(
            zip(feature_names, importances, strict=False),
            key=lambda item: item[1],
            reverse=True,
        )[:6]
        self.top_features = [
            {"feature": feature.replace("numeric__", "").replace("categorical__", ""), "importance": round(float(score), 4)}
            for feature, score in ranked
        ]
        self.pipeline = pipeline
        self.training_accuracy = accuracy
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "pipeline": pipeline,
                "accuracy": accuracy,
                "top_features": self.top_features,
            },
            self.model_path,
        )
        return {
            "status": "training_completed",
            "accuracy": accuracy,
            "samples": int(len(dataframe)),
            "top_features": self.top_features,
        }

    def predict(self, sample: dict[str, Any]) -> dict[str, Any]:
        if self.pipeline is None:
            raise RuntimeError("AI model is not trained.")
        frame = pd.DataFrame([sample])[MODEL_FEATURES]
        probabilities = self.pipeline.predict_proba(frame)[0]
        classes = list(self.pipeline.named_steps["model"].classes_)
        leakage_index = classes.index("leakage")
        probability = round(float(probabilities[leakage_index]), 4)
        confidence = round(float(max(probabilities)), 4)
        return {
            "attack_probability": probability,
            "risk_level": risk_level(probability),
            "model_confidence": confidence,
            "top_features": self.top_features,
            "training_accuracy": self.training_accuracy,
        }
