from __future__ import annotations

from hashlib import sha256

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from app.crypto.base import AlgorithmExecution, CryptoEngine


class RsaEngine(CryptoEngine):
    name = "RSA"

    def __init__(self) -> None:
        self.key = RSA.generate(2048)
        self.public_key = self.key.publickey()

    def execute(self, plaintext: bytes) -> AlgorithmExecution:
        cipher = PKCS1_OAEP.new(self.public_key)
        ciphertext = cipher.encrypt(plaintext[:86])
        fingerprint = sha256(self.key.export_key(format="DER")).hexdigest()
        intermediate = [value for value in ciphertext[:16]]
        return AlgorithmExecution(
            algorithm=self.name,
            plaintext=plaintext[:86],
            operation_output=ciphertext,
            intermediate_values=intermediate,
            secret_byte=fingerprint.encode("utf-8")[0],
            secret_fingerprint=fingerprint[:16],
        )
