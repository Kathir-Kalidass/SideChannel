from __future__ import annotations

from app.utils.helpers import clamp, normalize


class LeakageDetectionEngine:
    def compute_score(
        self,
        timing_variance: float,
        power_variance: float,
        cache_miss_rate: float,
        correlation_score: float,
    ) -> float:
        score = (
            normalize(timing_variance, 0.0, 0.18) * 0.26
            + normalize(power_variance, 0.0, 38.0) * 0.24
            + normalize(cache_miss_rate, 0.0, 16.0) * 0.2
            + clamp(correlation_score, 0.0, 1.0) * 0.3
        )
        return round(clamp(score, 0.0, 1.0), 4)
