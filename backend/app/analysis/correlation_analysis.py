from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from app.utils.helpers import hamming_weight


@dataclass(slots=True)
class AttackAnalysisResult:
    best_key_guess: str
    correlation_score: float
    correlation_profile: list[dict[str, float | str]]
    keys_tested: int
    attack_progress: float


class CorrelationAnalyzer:
    def analyze(
        self,
        samples: list[dict],
        total_runs: int,
    ) -> AttackAnalysisResult:
        if not samples:
            return AttackAnalysisResult(
                best_key_guess="00",
                correlation_score=0.0,
                correlation_profile=[],
                keys_tested=0,
                attack_progress=0.0,
            )

        plaintexts = np.array([sample["plaintext_byte"] for sample in samples], dtype=float)
        measured = np.array([sample["power_avg"] for sample in samples], dtype=float)
        scores: list[tuple[int, float]] = []

        for guess in range(256):
            predicted = np.array([hamming_weight(int(value) ^ guess) for value in plaintexts], dtype=float)
            if np.std(predicted) == 0 or np.std(measured) == 0:
                correlation = 0.0
            else:
                correlation = float(abs(np.corrcoef(predicted, measured)[0, 1]))
            if math.isnan(correlation):
                correlation = 0.0
            scores.append((guess, correlation))

        scores.sort(key=lambda item: item[1], reverse=True)
        best_guess, best_score = scores[0]
        top_profile = [
            {"key_guess": f"{guess:02X}", "correlation": round(score, 4)}
            for guess, score in scores[:16]
        ]
        progress = 0.0 if total_runs == 0 else min(100.0, (len(samples) / total_runs) * 100)
        return AttackAnalysisResult(
            best_key_guess=f"{best_guess:02X}",
            correlation_score=round(best_score, 4),
            correlation_profile=top_profile,
            keys_tested=min(256, max(16, len(samples) * 4)),
            attack_progress=round(progress, 2),
        )
