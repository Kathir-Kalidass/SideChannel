from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class TraceRecord(Base):
    __tablename__ = "trace_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    simulation_id: Mapped[str] = mapped_column(String(64), index=True)
    run_index: Mapped[int] = mapped_column(Integer, index=True)
    algorithm: Mapped[str] = mapped_column(String(32), index=True)
    attack_type: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(32), default="synthetic")
    label: Mapped[str] = mapped_column(String(32), default="secure")
    defense_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    defense_technique: Mapped[str] = mapped_column(String(64), default="none")
    attack_probability: Mapped[float] = mapped_column(Float, default=0.0)
    model_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(16), default="LOW")
    security_level: Mapped[str] = mapped_column(String(16), default="HIGH")
    execution_time_ms: Mapped[float] = mapped_column(Float)
    timing_variance: Mapped[float] = mapped_column(Float)
    cpu_usage_pct: Mapped[float] = mapped_column(Float)
    memory_usage_mb: Mapped[float] = mapped_column(Float)
    clock_cycles: Mapped[int] = mapped_column(Integer)
    power_avg: Mapped[float] = mapped_column(Float)
    power_peak: Mapped[float] = mapped_column(Float)
    power_variance: Mapped[float] = mapped_column(Float)
    hamming_weight_mean: Mapped[float] = mapped_column(Float)
    hamming_distance_mean: Mapped[float] = mapped_column(Float)
    cache_hits: Mapped[int] = mapped_column(Integer)
    cache_misses: Mapped[int] = mapped_column(Integer)
    cache_miss_rate: Mapped[float] = mapped_column(Float)
    correlation_score: Mapped[float] = mapped_column(Float)
    leakage_score: Mapped[float] = mapped_column(Float)
    plaintext_byte: Mapped[int] = mapped_column(Integer, default=0)
    key_guess: Mapped[str] = mapped_column(String(8), default="00")
    attack_progress: Mapped[float] = mapped_column(Float, default=0.0)
    leakage_reduction: Mapped[float] = mapped_column(Float, default=0.0)
    operation_output: Mapped[str] = mapped_column(String(1024), default="")
    power_trace: Mapped[list[float]] = mapped_column(JSON, default=list)
    correlation_profile: Mapped[list[dict]] = mapped_column(JSON, default=list)
    notes: Mapped[list[str]] = mapped_column(JSON, default=list)


class PaymentUser(Base):
    __tablename__ = "payment_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(128))
    upi: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    port: Mapped[int] = mapped_column(Integer, unique=True)
    otp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    vulnerability: Mapped[float] = mapped_column(Float, default=0.2)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    sender_user_id: Mapped[int] = mapped_column(Integer, index=True)
    sender_name: Mapped[str] = mapped_column(String(128))
    sender_upi: Mapped[str] = mapped_column(String(128), index=True)
    sender_port: Mapped[int] = mapped_column(Integer)
    receiver_user_id: Mapped[int] = mapped_column(Integer, index=True)
    receiver_name: Mapped[str] = mapped_column(String(128))
    receiver_upi: Mapped[str] = mapped_column(String(128), index=True)
    receiver_port: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)
    note: Mapped[str] = mapped_column(String(256), default="")
    algorithm: Mapped[str] = mapped_column(String(32), default="AES")
    decision: Mapped[str] = mapped_column(String(32), index=True)
    otp_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    risk: Mapped[float] = mapped_column(Float, default=0.0)
    leakage: Mapped[float] = mapped_column(Float, default=0.0)
    base_attack: Mapped[float] = mapped_column(Float, default=0.0)
    correlation: Mapped[float] = mapped_column(Float, default=0.0)
    defense: Mapped[bool] = mapped_column(Boolean, default=False)
    attacker_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    attacker_port: Mapped[int] = mapped_column(Integer, default=7103)
    theft_amount: Mapped[float] = mapped_column(Float, default=0.0)
    sender_otp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    receiver_otp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    timeline: Mapped[list[dict]] = mapped_column(JSON, default=list)


class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    drift_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    blocked_rate: Mapped[float] = mapped_column(Float, default=0.0)
    otp_rate: Mapped[float] = mapped_column(Float, default=0.0)
    theft_rate: Mapped[float] = mapped_column(Float, default=0.0)
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PairRiskPolicy(Base):
    __tablename__ = "pair_risk_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sender_user_id: Mapped[int] = mapped_column(Integer, index=True)
    receiver_user_id: Mapped[int] = mapped_column(Integer, index=True)
    pair_risk_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    block_threshold: Mapped[float] = mapped_column(Float, default=0.86)
    otp_threshold: Mapped[float] = mapped_column(Float, default=0.52)
    leakage_block_threshold: Mapped[float] = mapped_column(Float, default=0.78)
    leakage_otp_threshold: Mapped[float] = mapped_column(Float, default=0.56)
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
