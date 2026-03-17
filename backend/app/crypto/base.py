from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AlgorithmExecution:
    algorithm: str
    plaintext: bytes
    operation_output: bytes
    intermediate_values: list[int]
    secret_byte: int
    secret_fingerprint: str


class CryptoEngine:
    name: str

    def execute(self, plaintext: bytes) -> AlgorithmExecution:
        raise NotImplementedError
