from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AlgorithmLiteral = Literal["AES", "ChaCha20", "RSA", "ECC"]
AttackLiteral = Literal["power", "timing", "cache"]
DefenseLiteral = Literal["masking", "constant_time", "noise_injection"]


class SimulationConfig(BaseModel):
    algorithm: AlgorithmLiteral = "AES"
    attack_type: AttackLiteral = "power"
    runs: int = Field(default=1000, ge=10, le=5000)
    enable_ai: bool = True
    auto_defense: bool = True


class ManualDefenseRequest(BaseModel):
    technique: DefenseLiteral


class UploadResponse(BaseModel):
    imported_rows: int
    source: str


class PaymentUserOut(BaseModel):
    id: int
    username: str
    name: str
    upi: str
    port: int
    otp_enabled: bool
    vulnerability: float


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=3, max_length=128)


class PaymentHistoryRequest(BaseModel):
    sender_user_id: int
    sender_name: str = Field(min_length=2, max_length=128)
    sender_upi: str = Field(min_length=3, max_length=128)
    sender_port: int = Field(ge=1, le=65535)
    receiver_user_id: int
    receiver_name: str = Field(min_length=2, max_length=128)
    receiver_upi: str = Field(min_length=3, max_length=128)
    receiver_port: int = Field(ge=1, le=65535)
    amount: float = Field(gt=0, le=10_000_000)
    note: str = Field(default="", max_length=256)
    algorithm: AlgorithmLiteral = "AES"
    decision: str = Field(min_length=3, max_length=32)
    otp_verified: bool = False
    risk: float = Field(ge=0, le=1)
    leakage: float = Field(ge=0, le=1)
    base_attack: float = Field(ge=0, le=1)
    correlation: float = Field(ge=0, le=1)
    defense: bool = False
    attacker_enabled: bool = False
    attacker_port: int = Field(default=7103, ge=1, le=65535)
    theft_amount: float = Field(default=0, ge=0)
    sender_otp_enabled: bool = False
    receiver_otp_enabled: bool = False
    reasons: list[str] = Field(default_factory=list)
    timeline: list[dict] = Field(default_factory=list)
