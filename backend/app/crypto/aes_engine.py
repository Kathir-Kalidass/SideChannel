from __future__ import annotations

from hashlib import sha256

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from app.crypto.base import AlgorithmExecution, CryptoEngine


class AesEngine(CryptoEngine):
    name = "AES"

    def __init__(self, key: bytes | None = None) -> None:
        self.key = key or b"side-channel-aes"
        self.mode = AES.MODE_ECB

    def execute(self, plaintext: bytes) -> AlgorithmExecution:
        cipher = AES.new(self.key, self.mode)
        padded = pad(plaintext, AES.block_size)
        ciphertext = cipher.encrypt(padded)
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
