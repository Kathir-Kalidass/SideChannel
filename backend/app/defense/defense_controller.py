from __future__ import annotations

from app.defense.constant_time import apply_constant_time
from app.defense.masking import apply_masking
from app.defense.noise_injection import apply_noise_injection


class DefenseController:
    DEFAULT_TECHNIQUES = {
        "power": "masking",
        "timing": "constant_time",
        "cache": "noise_injection",
    }

    def choose_technique(self, attack_type: str) -> str:
        return self.DEFAULT_TECHNIQUES.get(attack_type, "masking")

    def apply(self, metrics: dict, technique: str) -> dict:
        adjusted = dict(metrics)
        if technique == "constant_time":
            adjusted = apply_constant_time(adjusted)
        elif technique == "noise_injection":
            adjusted = apply_noise_injection(adjusted)
        else:
            adjusted = apply_masking(adjusted)
        adjusted["defense_mode"] = True
        adjusted["defense_technique"] = technique
        return adjusted
