from pathlib import Path

from app.ai.attack_predictor import AttackPredictor, generate_synthetic_dataset
from app.analysis.leakage_detection import LeakageDetectionEngine


def test_leakage_detection_higher_for_vulnerable_profiles() -> None:
    engine = LeakageDetectionEngine()
    secure = engine.compute_score(0.03, 6.0, 3.2, 0.18)
    vulnerable = engine.compute_score(0.18, 24.0, 11.4, 0.82)
    assert vulnerable > secure


def test_attack_predictor_trains_and_predicts(tmp_path: Path) -> None:
    predictor = AttackPredictor(tmp_path / "model.joblib")
    training_response = predictor.train(generate_synthetic_dataset(180))
    prediction = predictor.predict(
        {
            "algorithm": "AES",
            "attack_type": "power",
            "defense_mode": False,
            "source": "synthetic",
            "execution_time_ms": 2.8,
            "timing_variance": 0.12,
            "cpu_usage_pct": 28.4,
            "memory_usage_mb": 31.2,
            "clock_cycles": 9200,
            "power_avg": 34.5,
            "power_peak": 44.0,
            "power_variance": 18.0,
            "hamming_weight_mean": 12.5,
            "hamming_distance_mean": 10.1,
            "cache_hits": 240,
            "cache_misses": 18,
            "cache_miss_rate": 7.0,
            "correlation_score": 0.74,
            "leakage_score": 0.78,
        }
    )
    assert training_response["accuracy"] > 0.7
    assert 0.0 <= prediction["attack_probability"] <= 1.0
