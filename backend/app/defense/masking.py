from __future__ import annotations


def apply_masking(metrics: dict) -> dict:
    metrics["power_avg"] = round(metrics["power_avg"] * 0.88, 4)
    metrics["power_peak"] = round(metrics["power_peak"] * 0.86, 4)
    metrics["power_variance"] = round(metrics["power_variance"] * 0.58, 4)
    metrics["hamming_weight_mean"] = round(metrics["hamming_weight_mean"] * 0.68, 4)
    metrics["hamming_distance_mean"] = round(metrics["hamming_distance_mean"] * 0.74, 4)
    metrics["power_trace"] = [round(value * 0.86, 4) for value in metrics["power_trace"]]
    return metrics
