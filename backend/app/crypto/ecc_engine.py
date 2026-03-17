from __future__ import annotations

from hashlib import sha256

from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS

from app.crypto.base import AlgorithmExecution, CryptoEngine


class EccEngine(CryptoEngine):
    name = "ECC"

    def __init__(self) -> None:
        self.key = ECC.generate(curve="P-256")

    def execute(self, plaintext: bytes) -> AlgorithmExecution:
        signer = DSS.new(self.key, "fips-186-3")
        digest = SHA256.new(plaintext)
        signature = signer.sign(digest)
        fingerprint = sha256(self.key.export_key(format="DER")).hexdigest()
        intermediate = [value for value in signature[:16]]
        return AlgorithmExecution(
            algorithm=self.name,
            plaintext=plaintext,
            operation_output=signature,
            intermediate_values=intermediate,
            secret_byte=fingerprint.encode("utf-8")[0],
            secret_fingerprint=fingerprint[:16],
        )
