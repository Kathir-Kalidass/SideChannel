from __future__ import annotations


def apply_constant_time(metrics: dict) -> dict:
    metrics["timing_variance"] = round(metrics["timing_variance"] * 0.35, 4)
    metrics["execution_time_ms"] = round(metrics["execution_time_ms"] + 0.25, 4)
    metrics["clock_cycles"] = int(metrics["clock_cycles"] * 1.06)
    metrics["cache_miss_rate"] = round(metrics["cache_miss_rate"] * 0.7, 4)
    metrics["cache_misses"] = max(1, int(metrics["cache_misses"] * 0.7))
    metrics["cache_hits"] = max(metrics["cache_hits"], metrics["cache_hits"] + 2)
    return metrics
