from __future__ import annotations

import math
from statistics import mean


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def hamming_weight(value: int) -> int:
    return bin(value & 0xFF).count("1")


def hamming_distance(left: int, right: int) -> int:
    return hamming_weight(left ^ right)


def normalize(value: float, lower: float, upper: float) -> float:
    if math.isclose(lower, upper):
        return 0.0
    return clamp((value - lower) / (upper - lower), 0.0, 1.0)


def average(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def risk_level(probability: float) -> str:
    if probability >= 0.75:
        return "HIGH"
    if probability >= 0.45:
        return "MEDIUM"
    return "LOW"


def security_level(probability: float) -> str:
    if probability < 0.35:
        return "HIGH"
    if probability < 0.7:
        return "MEDIUM"
    return "LOW"
