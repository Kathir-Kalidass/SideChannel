from app.crypto.aes_engine import AesEngine
from app.crypto.chacha20_engine import ChaCha20Engine
from app.crypto.ecc_engine import EccEngine
from app.crypto.rsa_engine import RsaEngine


def test_aes_engine_is_deterministic() -> None:
    engine = AesEngine()
    plaintext = b"demo-message-123"
    first = engine.execute(plaintext)
    second = engine.execute(plaintext)
    assert first.operation_output == second.operation_output
    assert len(first.intermediate_values) == 16


def test_other_crypto_engines_return_outputs() -> None:
    plaintext = b"side-channel-simulator"
    chacha = ChaCha20Engine().execute(plaintext)
    rsa = RsaEngine().execute(plaintext)
    ecc = EccEngine().execute(plaintext)
    assert chacha.operation_output
    assert rsa.operation_output
    assert ecc.operation_output
