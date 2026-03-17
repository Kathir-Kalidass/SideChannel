from __future__ import annotations

import random


class CacheSimulator:
    BASE_CACHE_MISSES = {
        "AES": 6,
        "ChaCha20": 4,
        "RSA": 15,
        "ECC": 12,
    }

    def simulate(self, algorithm: str, attack_type: str, defense_mode: bool) -> tuple[int, int, float]:
        total_accesses = random.randint(220, 360)
        misses = self.BASE_CACHE_MISSES.get(algorithm, 8)
        if attack_type == "cache":
            misses += random.randint(10, 24)
        else:
            misses += random.randint(0, 8)
        if defense_mode:
            misses = max(2, int(misses * 0.55))

        misses = min(misses, total_accesses - 1)
        hits = total_accesses - misses
        miss_rate = round((misses / total_accesses) * 100, 3)
        return hits, misses, miss_rate
