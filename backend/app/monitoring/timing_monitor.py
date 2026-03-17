from __future__ import annotations

import random


class TimingMonitor:
    BASE_EXECUTION_MS = {
        "AES": 1.8,
        "ChaCha20": 1.5,
        "RSA": 7.6,
        "ECC": 5.1,
    }

    def simulate(
        self,
        algorithm: str,
        attack_type: str,
        defense_mode: bool,
    ) -> tuple[float, float, int]:
        baseline = self.BASE_EXECUTION_MS.get(algorithm, 2.0)
        attack_weight = {"power": 0.12, "timing": 0.34, "cache": 0.22}.get(attack_type, 0.14)
        defense_modifier = 0.52 if defense_mode else 1.0
        timing_variance = max(0.012, random.uniform(0.04, 0.26) * attack_weight * defense_modifier)
        execution_time_ms = baseline + random.uniform(0.1, 0.7) + timing_variance * 2.1
        clock_cycles = int(execution_time_ms * 3200 + random.randint(25, 320))
        return execution_time_ms, timing_variance, clock_cycles
