from __future__ import annotations

import random


def apply_noise_injection(metrics: dict) -> dict:
    noisy_trace = []
    for value in metrics["power_trace"]:
        noisy_trace.append(round(max(0.0, value + random.uniform(-2.6, 2.6)), 4))
    metrics["power_trace"] = noisy_trace
    metrics["power_avg"] = round(sum(noisy_trace) / len(noisy_trace), 4)
    metrics["power_peak"] = round(max(noisy_trace), 4)
    metrics["power_variance"] = round(metrics["power_variance"] * 0.85, 4)
    return metrics
