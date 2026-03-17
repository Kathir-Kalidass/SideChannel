from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
from sqlalchemy import desc, select

from app.database.db import database
from app.database.models import PairRiskPolicy, PaymentRecord, PaymentUser, TraceRecord, UserRiskProfile


EXPORT_COLUMNS = [
    "simulation_id",
    "run_index",
    "algorithm",
    "attack_type",
    "source",
    "label",
    "defense_mode",
    "defense_technique",
    "execution_time_ms",
    "timing_variance",
    "cpu_usage_pct",
    "memory_usage_mb",
    "clock_cycles",
    "power_avg",
    "power_peak",
    "power_variance",
    "hamming_weight_mean",
    "hamming_distance_mean",
    "cache_hits",
    "cache_misses",
    "cache_miss_rate",
    "correlation_score",
    "leakage_score",
    "attack_probability",
    "model_confidence",
    "risk_level",
    "security_level",
]


class TraceService:
    _DEFAULT_THRESHOLDS = {
        "block_threshold": 0.86,
        "otp_threshold": 0.52,
        "leakage_block_threshold": 0.78,
        "leakage_otp_threshold": 0.56,
    }

    def ensure_seed_users(self) -> None:
        seeds = [
            {
                "username": "alice.pay",
                "password": "alice123",
                "name": "Alice Kumar",
                "upi": "alice@upi",
                "port": 7101,
                "otp_enabled": True,
                "vulnerability": 0.16,
            },
            {
                "username": "bob.recv",
                "password": "bob123",
                "name": "Bob Nair",
                "upi": "bob@upi",
                "port": 7102,
                "otp_enabled": False,
                "vulnerability": 0.28,
            },
            {
                "username": "charlie.ops",
                "password": "charlie123",
                "name": "Charlie Das",
                "upi": "charlie@upi",
                "port": 7104,
                "otp_enabled": True,
                "vulnerability": 0.22,
            },
        ]

        with database.session() as db:
            for seed in seeds:
                existing = db.execute(
                    select(PaymentUser).where(PaymentUser.username == seed["username"])
                ).scalar_one_or_none()
                if existing:
                    continue
                db.add(PaymentUser(**seed))

    def list_payment_users(self) -> list[dict[str, Any]]:
        with database.session() as db:
            users = db.execute(select(PaymentUser).order_by(PaymentUser.id.asc())).scalars().all()
        return [self._serialize_user(user) for user in users]

    def authenticate_payment_user(self, username: str, password: str) -> dict[str, Any] | None:
        with database.session() as db:
            user = db.execute(
                select(PaymentUser).where(PaymentUser.username == username)
            ).scalar_one_or_none()
        if not user or user.password != password:
            return None
        return self._serialize_user(user)

    def save_payment_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        with database.session() as db:
            record = PaymentRecord(**payload)
            db.add(record)
            db.flush()
            db.refresh(record)

            # Feed transaction outcomes back into AI training corpus.
            trace = TraceRecord(
                simulation_id=f"payment-{record.id}",
                run_index=1,
                algorithm=record.algorithm,
                attack_type="power",
                source="payment_history",
                label="leakage" if record.decision in {"BLOCKED", "THEFTED"} else "secure",
                defense_mode=record.defense,
                defense_technique="none",
                attack_probability=record.risk,
                model_confidence=0.85,
                risk_level="HIGH" if record.risk >= 0.75 else "MEDIUM" if record.risk >= 0.45 else "LOW",
                security_level="LOW" if record.decision in {"BLOCKED", "THEFTED"} else "HIGH",
                execution_time_ms=3.0 + (record.risk * 5),
                timing_variance=max(0.01, record.leakage * 0.2),
                cpu_usage_pct=22 + (record.risk * 30),
                memory_usage_mb=20 + (record.risk * 40),
                clock_cycles=int(6000 + (record.risk * 9000)),
                power_avg=26 + (record.leakage * 12),
                power_peak=33 + (record.leakage * 18),
                power_variance=8 + (record.leakage * 26),
                hamming_weight_mean=4 + (record.leakage * 10),
                hamming_distance_mean=3 + (record.leakage * 10),
                cache_hits=max(120, int(320 - (record.risk * 100))),
                cache_misses=max(1, int(6 + (record.risk * 26))),
                cache_miss_rate=min(100, record.risk * 35),
                correlation_score=record.correlation,
                leakage_score=record.leakage,
                plaintext_byte=0,
                key_guess="00",
                attack_progress=100.0,
                leakage_reduction=0.0,
                operation_output="payment-history",
                power_trace=[point.get("power", 0) for point in (record.timeline or []) if isinstance(point, dict)],
                correlation_profile=[],
                notes=record.reasons or [f"Payment decision {record.decision}"],
            )
            db.add(trace)

            self._update_adaptive_profiles(db, record)

            return self._serialize_payment(record)

    def get_adaptive_policy(self, sender_user_id: int, receiver_user_id: int) -> dict[str, Any]:
        with database.session() as db:
            sender = db.execute(
                select(UserRiskProfile).where(UserRiskProfile.user_id == sender_user_id)
            ).scalar_one_or_none()
            receiver = db.execute(
                select(UserRiskProfile).where(UserRiskProfile.user_id == receiver_user_id)
            ).scalar_one_or_none()
            pair = db.execute(
                select(PairRiskPolicy).where(
                    PairRiskPolicy.sender_user_id == sender_user_id,
                    PairRiskPolicy.receiver_user_id == receiver_user_id,
                )
            ).scalar_one_or_none()

        sender_multiplier = sender.risk_multiplier if sender else 1.0
        receiver_multiplier = receiver.risk_multiplier if receiver else 1.0
        pair_multiplier = pair.pair_risk_multiplier if pair else 1.0

        thresholds = {
            "block_threshold": pair.block_threshold if pair else self._DEFAULT_THRESHOLDS["block_threshold"],
            "otp_threshold": pair.otp_threshold if pair else self._DEFAULT_THRESHOLDS["otp_threshold"],
            "leakage_block_threshold": (
                pair.leakage_block_threshold if pair else self._DEFAULT_THRESHOLDS["leakage_block_threshold"]
            ),
            "leakage_otp_threshold": pair.leakage_otp_threshold if pair else self._DEFAULT_THRESHOLDS["leakage_otp_threshold"],
        }

        return {
            "sender_user_id": sender_user_id,
            "receiver_user_id": receiver_user_id,
            "sender": {
                "drift_score": round(sender.drift_score, 4) if sender else 0.0,
                "risk_multiplier": round(sender_multiplier, 4),
                "total_transactions": sender.total_transactions if sender else 0,
            },
            "receiver": {
                "drift_score": round(receiver.drift_score, 4) if receiver else 0.0,
                "risk_multiplier": round(receiver_multiplier, 4),
                "total_transactions": receiver.total_transactions if receiver else 0,
            },
            "pair": {
                "risk_multiplier": round(pair_multiplier, 4),
                "total_transactions": pair.total_transactions if pair else 0,
            },
            "thresholds": {key: round(value, 4) for key, value in thresholds.items()},
        }

    def payment_history(self, limit: int = 200) -> list[dict[str, Any]]:
        with database.session() as db:
            records = (
                db.execute(select(PaymentRecord).order_by(desc(PaymentRecord.id)).limit(limit)).scalars().all()
            )
        return [self._serialize_payment(record) for record in records]

    def save_trace(self, payload: dict[str, Any]) -> dict[str, Any]:
        allowed_columns = set(TraceRecord.__table__.columns.keys())
        filtered_payload = {key: value for key, value in payload.items() if key in allowed_columns}
        with database.session() as db:
            record = TraceRecord(**filtered_payload)
            db.add(record)
            db.flush()
            db.refresh(record)
            return self._serialize(record)

    def get_latest(self) -> dict[str, Any] | None:
        with database.session() as db:
            record = db.execute(select(TraceRecord).order_by(desc(TraceRecord.id)).limit(1)).scalar_one_or_none()
            return self._serialize(record) if record else None

    def history(self, limit: int = 60) -> list[dict[str, Any]]:
        with database.session() as db:
            records = (
                db.execute(select(TraceRecord).order_by(desc(TraceRecord.id)).limit(limit)).scalars().all()
            )
            return [self._serialize(record) for record in reversed(records)]

    def load_training_frame(self) -> pd.DataFrame:
        with database.session() as db:
            records = db.execute(select(TraceRecord)).scalars().all()
        if not records:
            return pd.DataFrame()
        data = [self._serialize(record) for record in records]
        return pd.DataFrame(data)

    def export_csv(self) -> str:
        frame = self.load_training_frame()
        if frame.empty:
            frame = pd.DataFrame(columns=EXPORT_COLUMNS)
        else:
            frame = frame[[column for column in EXPORT_COLUMNS if column in frame.columns]]
        output = StringIO()
        frame.to_csv(output, index=False)
        return output.getvalue()

    def import_dataframe(self, dataframe: pd.DataFrame, source: str = "ascad") -> int:
        required_defaults = {
            "simulation_id": "external-import",
            "run_index": 0,
            "algorithm": "AES",
            "attack_type": "power",
            "source": source,
            "label": "leakage",
            "defense_mode": False,
            "defense_technique": "none",
            "attack_probability": 0.0,
            "model_confidence": 0.0,
            "risk_level": "LOW",
            "security_level": "MEDIUM",
            "execution_time_ms": 0.0,
            "timing_variance": 0.0,
            "cpu_usage_pct": 0.0,
            "memory_usage_mb": 0.0,
            "clock_cycles": 0,
            "power_avg": 0.0,
            "power_peak": 0.0,
            "power_variance": 0.0,
            "hamming_weight_mean": 0.0,
            "hamming_distance_mean": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_miss_rate": 0.0,
            "correlation_score": 0.0,
            "leakage_score": 0.0,
            "plaintext_byte": 0,
            "key_guess": "00",
            "attack_progress": 0.0,
            "leakage_reduction": 0.0,
            "operation_output": "",
            "power_trace": [],
            "correlation_profile": [],
            "notes": ["Imported benchmark sample"],
        }

        imported = 0
        with database.session() as db:
            for row in dataframe.to_dict(orient="records"):
                payload = {**required_defaults, **row}
                db.add(TraceRecord(**payload))
                imported += 1
        return imported

    @staticmethod
    def _serialize(record: TraceRecord | None) -> dict[str, Any]:
        if record is None:
            return {}
        return {
            "id": record.id,
            "created_at": record.created_at.isoformat(),
            "simulation_id": record.simulation_id,
            "run_index": record.run_index,
            "algorithm": record.algorithm,
            "attack_type": record.attack_type,
            "source": record.source,
            "label": record.label,
            "defense_mode": record.defense_mode,
            "defense_technique": record.defense_technique,
            "attack_probability": record.attack_probability,
            "model_confidence": record.model_confidence,
            "risk_level": record.risk_level,
            "security_level": record.security_level,
            "execution_time_ms": record.execution_time_ms,
            "timing_variance": record.timing_variance,
            "cpu_usage_pct": record.cpu_usage_pct,
            "memory_usage_mb": record.memory_usage_mb,
            "clock_cycles": record.clock_cycles,
            "power_avg": record.power_avg,
            "power_peak": record.power_peak,
            "power_variance": record.power_variance,
            "hamming_weight_mean": record.hamming_weight_mean,
            "hamming_distance_mean": record.hamming_distance_mean,
            "cache_hits": record.cache_hits,
            "cache_misses": record.cache_misses,
            "cache_miss_rate": record.cache_miss_rate,
            "correlation_score": record.correlation_score,
            "leakage_score": record.leakage_score,
            "plaintext_byte": record.plaintext_byte,
            "key_guess": record.key_guess,
            "attack_progress": record.attack_progress,
            "leakage_reduction": record.leakage_reduction,
            "operation_output": record.operation_output,
            "power_trace": record.power_trace,
            "correlation_profile": record.correlation_profile,
            "notes": record.notes,
        }

    @staticmethod
    def _serialize_user(user: PaymentUser) -> dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "upi": user.upi,
            "port": user.port,
            "otp_enabled": user.otp_enabled,
            "vulnerability": user.vulnerability,
        }

    @staticmethod
    def _serialize_payment(record: PaymentRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "created_at": record.created_at.isoformat(),
            "sender_user_id": record.sender_user_id,
            "sender_name": record.sender_name,
            "sender_upi": record.sender_upi,
            "sender_port": record.sender_port,
            "receiver_user_id": record.receiver_user_id,
            "receiver_name": record.receiver_name,
            "receiver_upi": record.receiver_upi,
            "receiver_port": record.receiver_port,
            "amount": record.amount,
            "note": record.note,
            "algorithm": record.algorithm,
            "decision": record.decision,
            "otp_verified": record.otp_verified,
            "risk": record.risk,
            "leakage": record.leakage,
            "base_attack": record.base_attack,
            "correlation": record.correlation,
            "defense": record.defense,
            "attacker_enabled": record.attacker_enabled,
            "attacker_port": record.attacker_port,
            "theft_amount": record.theft_amount,
            "sender_otp_enabled": record.sender_otp_enabled,
            "receiver_otp_enabled": record.receiver_otp_enabled,
            "reasons": record.reasons,
            "timeline": record.timeline,
        }

    def _update_adaptive_profiles(self, db, record: PaymentRecord) -> None:
        sender_profile = db.execute(
            select(UserRiskProfile).where(UserRiskProfile.user_id == record.sender_user_id)
        ).scalar_one_or_none()
        if sender_profile is None:
            sender_profile = UserRiskProfile(user_id=record.sender_user_id)
            db.add(sender_profile)

        receiver_profile = db.execute(
            select(UserRiskProfile).where(UserRiskProfile.user_id == record.receiver_user_id)
        ).scalar_one_or_none()
        if receiver_profile is None:
            receiver_profile = UserRiskProfile(user_id=record.receiver_user_id)
            db.add(receiver_profile)

        pair_policy = db.execute(
            select(PairRiskPolicy).where(
                PairRiskPolicy.sender_user_id == record.sender_user_id,
                PairRiskPolicy.receiver_user_id == record.receiver_user_id,
            )
        ).scalar_one_or_none()
        if pair_policy is None:
            pair_policy = PairRiskPolicy(
                sender_user_id=record.sender_user_id,
                receiver_user_id=record.receiver_user_id,
            )
            db.add(pair_policy)

        self._apply_profile_update(sender_profile, record)
        self._apply_profile_update(receiver_profile, record)
        self._apply_pair_policy_update(pair_policy, record)

    def _apply_profile_update(self, profile: UserRiskProfile, record: PaymentRecord) -> None:
        alpha = 0.22
        event_score = self._event_score(record)
        profile.total_transactions += 1
        profile.drift_score = ((1 - alpha) * profile.drift_score) + (alpha * event_score)

        is_blocked = 1.0 if record.decision == "BLOCKED" else 0.0
        is_otp = 1.0 if record.decision == "OTP" else 0.0
        is_theft = 1.0 if record.decision == "THEFTED" else 0.0

        profile.blocked_rate = ((1 - alpha) * profile.blocked_rate) + (alpha * is_blocked)
        profile.otp_rate = ((1 - alpha) * profile.otp_rate) + (alpha * is_otp)
        profile.theft_rate = ((1 - alpha) * profile.theft_rate) + (alpha * is_theft)

        multiplier = 1.0 + (profile.drift_score * 0.3) + (profile.theft_rate * 0.4) + (profile.blocked_rate * 0.15)
        profile.risk_multiplier = max(0.8, min(1.9, multiplier))

    def _apply_pair_policy_update(self, pair: PairRiskPolicy, record: PaymentRecord) -> None:
        alpha = 0.2
        event_score = self._event_score(record)
        pair.total_transactions += 1
        pair.pair_risk_multiplier = max(
            0.85,
            min(2.1, ((1 - alpha) * pair.pair_risk_multiplier) + (alpha * (1.0 + (event_score * 0.55)))),
        )

        baseline_block = self._DEFAULT_THRESHOLDS["block_threshold"]
        baseline_otp = self._DEFAULT_THRESHOLDS["otp_threshold"]
        baseline_leakage_block = self._DEFAULT_THRESHOLDS["leakage_block_threshold"]
        baseline_leakage_otp = self._DEFAULT_THRESHOLDS["leakage_otp_threshold"]

        stress = max(0.0, min(0.35, (pair.pair_risk_multiplier - 1.0) * 0.24))
        pair.block_threshold = max(0.65, min(0.95, baseline_block - stress))
        pair.otp_threshold = max(0.38, min(0.8, baseline_otp - (stress * 0.9)))
        pair.leakage_block_threshold = max(0.55, min(0.92, baseline_leakage_block - (stress * 0.8)))
        pair.leakage_otp_threshold = max(0.42, min(0.8, baseline_leakage_otp - (stress * 0.75)))

    @staticmethod
    def _event_score(record: PaymentRecord) -> float:
        base = (record.risk * 0.6) + (record.leakage * 0.4)
        if record.decision == "THEFTED":
            base += 0.25
        elif record.decision == "BLOCKED":
            base += 0.16
        elif record.decision == "OTP":
            base += 0.08
        return max(0.0, min(1.0, base))
