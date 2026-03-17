from __future__ import annotations

import random
from statistics import mean, pvariance

from app.utils.helpers import hamming_distance, hamming_weight


class PowerSimulator:
    def simulate(
        self,
        intermediate_values: list[int],
        attack_type: str,
        defense_mode: bool,
    ) -> dict[str, float | list[float]]:
        attack_bias = {"power": 1.35, "timing": 0.9, "cache": 1.0}.get(attack_type, 1.0)
        noise_factor = 0.65 if defense_mode else 0.25
        power_trace: list[float] = []
        weights: list[int] = []
        distances: list[int] = []

        previous = intermediate_values[0] if intermediate_values else 0
        for value in intermediate_values:
            hw = hamming_weight(value)
            hd = hamming_distance(previous, value)
            weights.append(hw)
            distances.append(hd)
            leakage = (hw * 2.1 + hd * 0.75) * attack_bias
            jitter = random.uniform(-4.2, 4.2) * noise_factor
            power_trace.append(max(0.0, leakage + 18 + jitter))
            previous = value

        return {
            "power_trace": power_trace,
            "power_avg": float(mean(power_trace)) if power_trace else 0.0,
            "power_peak": max(power_trace, default=0.0),
            "power_variance": float(pvariance(power_trace)) if len(power_trace) > 1 else 0.0,
            "hamming_weight_mean": float(mean(weights)) if weights else 0.0,
            "hamming_distance_mean": float(mean(distances)) if distances else 0.0,
        }
