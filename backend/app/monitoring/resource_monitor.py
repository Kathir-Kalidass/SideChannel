from __future__ import annotations

import random


class ResourceMonitor:
    def simulate(self, algorithm: str, defense_mode: bool) -> tuple[float, float]:
        cpu_map = {
            "AES": (14.0, 28.0),
            "ChaCha20": (11.0, 24.0),
            "RSA": (30.0, 58.0),
            "ECC": (22.0, 46.0),
        }
        memory_map = {
            "AES": (18.0, 40.0),
            "ChaCha20": (16.0, 34.0),
            "RSA": (34.0, 72.0),
            "ECC": (28.0, 56.0),
        }
        cpu_low, cpu_high = cpu_map.get(algorithm, (10.0, 24.0))
        mem_low, mem_high = memory_map.get(algorithm, (16.0, 32.0))
        cpu_usage = random.uniform(cpu_low, cpu_high)
        memory_usage = random.uniform(mem_low, mem_high)
        if defense_mode:
            cpu_usage += 4.2
            memory_usage += 2.8
        return round(cpu_usage, 3), round(memory_usage, 3)
