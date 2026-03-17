from __future__ import annotations

from hashlib import sha256

from Crypto.Cipher import ChaCha20

from app.crypto.base import AlgorithmExecution, CryptoEngine


class ChaCha20Engine(CryptoEngine):
    name = "ChaCha20"

    def __init__(self, key: bytes | None = None, nonce: bytes | None = None) -> None:
        self.key = key or sha256(b"side-channel-chacha20").digest()
        self.nonce = nonce or b"traceLab1234"

    def execute(self, plaintext: bytes) -> AlgorithmExecution:
        cipher = ChaCha20.new(key=self.key, nonce=self.nonce)
        ciphertext = cipher.encrypt(plaintext)
        intermediate = [value for value in ciphertext[:16]]
        fingerprint = sha256(self.key).hexdigest()
        return AlgorithmExecution(
            algorithm=self.name,
            plaintext=plaintext,
            operation_output=ciphertext,
            intermediate_values=intermediate,
            secret_byte=self.key[0],
            secret_fingerprint=fingerprint[:16],
        )
