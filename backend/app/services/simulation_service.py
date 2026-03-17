from __future__ import annotations

import asyncio
import secrets
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pandas as pd

from app.ai.attack_predictor import AttackPredictor, generate_synthetic_dataset
from app.analysis.correlation_analysis import CorrelationAnalyzer
from app.analysis.leakage_detection import LeakageDetectionEngine
from app.config import Settings
from app.crypto.aes_engine import AesEngine
from app.crypto.chacha20_engine import ChaCha20Engine
from app.crypto.ecc_engine import EccEngine
from app.crypto.rsa_engine import RsaEngine
from app.defense.defense_controller import DefenseController
from app.monitoring.cache_simulator import CacheSimulator
from app.monitoring.power_simulator import PowerSimulator
from app.monitoring.resource_monitor import ResourceMonitor
from app.monitoring.timing_monitor import TimingMonitor
from app.services.trace_service import TraceService
from app.utils.helpers import clamp, risk_level, security_level


@dataclass(slots=True)
class SimulationSnapshot:
    running: bool = False
    simulation_id: str | None = None
    algorithm: str = "AES"
    attack_type: str = "power"
    total_runs: int = 0
    runs_completed: int = 0
    enable_ai: bool = True
    auto_defense: bool = True
    attack_running: bool = False
    defense_mode: bool = False
    defense_technique: str = "none"
    leakage_reduction: float = 0.0
    security_level: str = "HIGH"
    current_metrics: dict[str, Any] = field(default_factory=dict)
    ai_prediction: dict[str, Any] = field(default_factory=dict)
    attack_status: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)


class SimulationService:
    def __init__(
        self,
        settings: Settings,
        trace_service: TraceService,
        predictor: AttackPredictor,
    ) -> None:
        self.settings = settings
        self.trace_service = trace_service
        self.predictor = predictor
        self.engines = {
            "AES": AesEngine(),
            "ChaCha20": ChaCha20Engine(),
            "RSA": RsaEngine(),
            "ECC": EccEngine(),
        }
        self.timing_monitor = TimingMonitor()
        self.power_simulator = PowerSimulator()
        self.cache_simulator = CacheSimulator()
        self.resource_monitor = ResourceMonitor()
        self.leakage_engine = LeakageDetectionEngine()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.defense_controller = DefenseController()
        self.snapshot = SimulationSnapshot()
        self.session_samples: list[dict[str, Any]] = []
        self.recent_logs: deque[str] = deque(maxlen=48)
        self.subscribers: set[asyncio.Queue] = set()
        self.task: asyncio.Task | None = None

    async def initialize(self) -> None:
        self.trace_service.ensure_seed_users()
        if self.settings.auto_train_on_startup:
            self.predictor.ensure_model(self.settings.synthetic_dataset_size)

    async def start(self, config: dict[str, Any]) -> dict[str, Any]:
        await self.stop()
        if config.get("enable_ai") and self.settings.ai_retrain_on_simulation_start:
            try:
                response = await self.train_model()
                self._log(
                    "Auto AI retraining completed before simulation start "
                    f"(samples={response['samples']}, accuracy={response['accuracy']:.4f})."
                )
            except Exception as exc:  # pragma: no cover - defensive runtime fallback
                self._log(f"Auto AI retraining skipped due to error: {exc}")
        simulation_id = uuid4().hex[:10]
        self.session_samples = []
        self.recent_logs.clear()
        self.snapshot = SimulationSnapshot(
            running=True,
            simulation_id=simulation_id,
            algorithm=config["algorithm"],
            attack_type=config["attack_type"],
            total_runs=config["runs"],
            runs_completed=0,
            enable_ai=config["enable_ai"],
            auto_defense=config["auto_defense"],
            attack_running=True,
        )
        self._log(f"Simulation {simulation_id} started for {config['algorithm']} ({config['attack_type']}).")
        self.task = asyncio.create_task(self._simulation_loop())
        return self.status()

    async def stop(self) -> dict[str, Any]:
        self.snapshot.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        if self.snapshot.simulation_id:
            self._log(f"Simulation {self.snapshot.simulation_id} stopped.")
        return self.status()

    async def reset(self) -> dict[str, Any]:
        await self.stop()
        self.session_samples = []
        self.recent_logs.clear()
        self.snapshot = SimulationSnapshot()
        return self.status()

    async def start_attack(self) -> dict[str, Any]:
        self.snapshot.attack_running = True
        self._log("Attack analysis started.")
        return self.attack_status()

    async def activate_defense(self, technique: str | None = None) -> dict[str, Any]:
        chosen = technique or self.defense_controller.choose_technique(self.snapshot.attack_type)
        self.snapshot.defense_mode = True
        self.snapshot.defense_technique = chosen
        self._log(f"Defense manually activated: {chosen}.")
        return self.defense_status()

    async def disable_defense(self) -> dict[str, Any]:
        self.snapshot.defense_mode = False
        self.snapshot.defense_technique = "none"
        self.snapshot.leakage_reduction = 0.0
        self._log("Defense disabled.")
        return self.defense_status()

    def status(self) -> dict[str, Any]:
        return {
            "status": "running" if self.snapshot.running else "stopped",
            "simulation_id": self.snapshot.simulation_id,
            "algorithm": self.snapshot.algorithm,
            "attack_type": self.snapshot.attack_type,
            "runs_completed": self.snapshot.runs_completed,
            "total_runs": self.snapshot.total_runs,
            "enable_ai": self.snapshot.enable_ai,
            "auto_defense": self.snapshot.auto_defense,
            "defense_mode": self.snapshot.defense_mode,
            "defense_technique": self.snapshot.defense_technique,
        }

    def current_metrics(self) -> dict[str, Any]:
        if self.snapshot.current_metrics:
            return deepcopy(self.snapshot.current_metrics)
        return self.trace_service.get_latest() or {}

    def history(self, limit: int = 60) -> list[dict[str, Any]]:
        return self.trace_service.history(limit)

    def attack_status(self) -> dict[str, Any]:
        if self.snapshot.attack_status:
            return deepcopy(self.snapshot.attack_status)
        return {
            "keys_tested": 0,
            "best_key_guess": "00",
            "correlation": 0.0,
            "attack_progress": 0.0,
            "correlation_profile": [],
        }

    def ai_prediction(self) -> dict[str, Any]:
        if self.snapshot.ai_prediction:
            return deepcopy(self.snapshot.ai_prediction)
        return {
            "attack_probability": 0.0,
            "risk_level": "LOW",
            "model_confidence": 0.0,
            "top_features": self.predictor.top_features,
            "training_accuracy": self.predictor.training_accuracy,
        }

    def defense_status(self) -> dict[str, Any]:
        prediction = self.ai_prediction()
        return {
            "defense_mode": "ACTIVE" if self.snapshot.defense_mode else "INACTIVE",
            "technique": self.snapshot.defense_technique,
            "security_level": self.snapshot.security_level,
            "leakage_reduction": round(self.snapshot.leakage_reduction, 4),
            "attack_probability": prediction["attack_probability"],
        }

    def event_log(self) -> list[str]:
        return list(self.recent_logs)

    def get_dashboard_frame(self) -> dict[str, Any]:
        history = self.history(30)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "simulation": self.status(),
            "current": self.current_metrics(),
            "attack": self.attack_status(),
            "ai": self.ai_prediction(),
            "defense": self.defense_status(),
            "history": history,
            "logs": self.event_log(),
        }

    async def train_model(self) -> dict[str, Any]:
        synthetic = generate_synthetic_dataset(self.settings.synthetic_dataset_size)
        historic = self.trace_service.load_training_frame()
        if not historic.empty:
            training_frame = pd.concat([synthetic, historic], ignore_index=True, sort=False).fillna(0)
        else:
            training_frame = synthetic
        response = self.predictor.train(training_frame)
        self._log(f"AI model trained on {response['samples']} samples.")
        return response

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=4)
        self.subscribers.add(queue)
        await queue.put(self.get_dashboard_frame())
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self.subscribers.discard(queue)

    async def _simulation_loop(self) -> None:
        while self.snapshot.running and self.snapshot.runs_completed < self.snapshot.total_runs:
            remaining = self.snapshot.total_runs - self.snapshot.runs_completed
            batch_size = min(self.settings.simulation_batch_size, remaining)
            batch: list[dict[str, Any]] = []
            for _ in range(batch_size):
                sample = self._simulate_run()
                self.session_samples.append(
                    {
                        "plaintext_byte": sample["plaintext_byte"],
                        "power_avg": sample["power_avg"],
                    }
                )
                batch.append(sample)
                self.snapshot.runs_completed += 1

            attack_result = self.correlation_analyzer.analyze(
                self.session_samples,
                self.snapshot.total_runs,
            )
            self.snapshot.attack_status = {
                "keys_tested": attack_result.keys_tested,
                "best_key_guess": attack_result.best_key_guess,
                "correlation": attack_result.correlation_score,
                "attack_progress": attack_result.attack_progress,
                "correlation_profile": attack_result.correlation_profile,
            }

            for index, sample in enumerate(batch):
                sample["key_guess"] = attack_result.best_key_guess
                sample["attack_progress"] = attack_result.attack_progress
                sample["correlation_profile"] = attack_result.correlation_profile
                if index == len(batch) - 1:
                    sample["correlation_score"] = attack_result.correlation_score
                    sample["notes"] = sample["notes"] + [
                        f"Attack best guess {attack_result.best_key_guess} with score {attack_result.correlation_score:.2f}"
                    ]
                stored = self.trace_service.save_trace(sample)
                if index == len(batch) - 1:
                    self.snapshot.current_metrics = stored

            prediction = self.snapshot.ai_prediction
            if isinstance(prediction, dict):
                probability = prediction.get("attack_probability", 0.0)
            else:
                probability = 0.0
            self.snapshot.security_level = security_level(probability)
            await self._broadcast()

            if self.snapshot.runs_completed >= self.snapshot.total_runs:
                break
            await asyncio.sleep(self.settings.simulation_tick_seconds)

        self.snapshot.running = False
        self._log("Simulation completed.")
        await self._broadcast()

    def _simulate_run(self) -> dict[str, Any]:
        algorithm = self.snapshot.algorithm
        attack_type = self.snapshot.attack_type
        defense_mode = self.snapshot.defense_mode
        engine = self.engines[algorithm]
        plaintext = secrets.token_bytes(32)
        execution = engine.execute(plaintext)
        execution_time_ms, timing_variance, clock_cycles = self.timing_monitor.simulate(
            algorithm,
            attack_type,
            defense_mode,
        )
        power_metrics = self.power_simulator.simulate(
            execution.intermediate_values,
            attack_type,
            defense_mode,
        )
        cache_hits, cache_misses, cache_miss_rate = self.cache_simulator.simulate(
            algorithm,
            attack_type,
            defense_mode,
        )
        cpu_usage_pct, memory_usage_mb = self.resource_monitor.simulate(
            algorithm,
            defense_mode,
        )
        correlation_score = self._estimate_correlation(
            power_avg=power_metrics["power_avg"],
            power_variance=power_metrics["power_variance"],
            attack_type=attack_type,
            defense_mode=defense_mode,
            cache_miss_rate=cache_miss_rate,
            timing_variance=timing_variance,
        )
        leakage_score = self.leakage_engine.compute_score(
            timing_variance=timing_variance,
            power_variance=float(power_metrics["power_variance"]),
            cache_miss_rate=cache_miss_rate,
            correlation_score=correlation_score,
        )

        sample = {
            "simulation_id": self.snapshot.simulation_id or "idle",
            "run_index": self.snapshot.runs_completed + 1,
            "algorithm": algorithm,
            "attack_type": attack_type,
            "source": "synthetic",
            "label": "leakage" if leakage_score >= 0.55 else "secure",
            "defense_mode": defense_mode,
            "defense_technique": self.snapshot.defense_technique,
            "execution_time_ms": round(execution_time_ms, 4),
            "timing_variance": round(timing_variance, 4),
            "cpu_usage_pct": round(cpu_usage_pct, 4),
            "memory_usage_mb": round(memory_usage_mb, 4),
            "clock_cycles": clock_cycles,
            "power_avg": round(float(power_metrics["power_avg"]), 4),
            "power_peak": round(float(power_metrics["power_peak"]), 4),
            "power_variance": round(float(power_metrics["power_variance"]), 4),
            "hamming_weight_mean": round(float(power_metrics["hamming_weight_mean"]), 4),
            "hamming_distance_mean": round(float(power_metrics["hamming_distance_mean"]), 4),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_miss_rate": round(cache_miss_rate, 4),
            "correlation_score": round(correlation_score, 4),
            "leakage_score": round(leakage_score, 4),
            "plaintext_byte": int(plaintext[0]),
            "key_guess": "00",
            "attack_progress": 0.0,
            "leakage_reduction": 0.0,
            "operation_output": execution.operation_output.hex(),
            "power_trace": [round(value, 4) for value in power_metrics["power_trace"]],
            "correlation_profile": [],
            "notes": [f"Secret fingerprint {execution.secret_fingerprint}"],
        }

        ai_sample = {
            "algorithm": sample["algorithm"],
            "attack_type": sample["attack_type"],
            "defense_mode": sample["defense_mode"],
            "source": sample["source"],
            "execution_time_ms": sample["execution_time_ms"],
            "timing_variance": sample["timing_variance"],
            "cpu_usage_pct": sample["cpu_usage_pct"],
            "memory_usage_mb": sample["memory_usage_mb"],
            "clock_cycles": sample["clock_cycles"],
            "power_avg": sample["power_avg"],
            "power_peak": sample["power_peak"],
            "power_variance": sample["power_variance"],
            "hamming_weight_mean": sample["hamming_weight_mean"],
            "hamming_distance_mean": sample["hamming_distance_mean"],
            "cache_hits": sample["cache_hits"],
            "cache_misses": sample["cache_misses"],
            "cache_miss_rate": sample["cache_miss_rate"],
            "correlation_score": sample["correlation_score"],
            "leakage_score": sample["leakage_score"],
        }
        prediction = self.predictor.predict(ai_sample) if self.snapshot.enable_ai else self._heuristic_prediction(sample)
        sample.update(prediction)
        self.snapshot.ai_prediction = prediction
        self.snapshot.security_level = security_level(prediction["attack_probability"])

        if (
            self.snapshot.auto_defense
            and not self.snapshot.defense_mode
            and (
                sample["attack_probability"] >= 0.7 or sample["leakage_score"] >= 0.65
            )
        ):
            before = sample["leakage_score"]
            technique = self.defense_controller.choose_technique(attack_type)
            defended = self.defense_controller.apply(sample, technique)
            defended["correlation_score"] = round(defended["correlation_score"] * 0.68, 4)
            defended["leakage_score"] = self.leakage_engine.compute_score(
                timing_variance=defended["timing_variance"],
                power_variance=defended["power_variance"],
                cache_miss_rate=defended["cache_miss_rate"],
                correlation_score=defended["correlation_score"],
            )
            defended_prediction = self.predictor.predict(
                {
                    **ai_sample,
                    "defense_mode": True,
                    "power_avg": defended["power_avg"],
                    "power_peak": defended["power_peak"],
                    "power_variance": defended["power_variance"],
                    "hamming_weight_mean": defended["hamming_weight_mean"],
                    "hamming_distance_mean": defended["hamming_distance_mean"],
                    "cache_hits": defended["cache_hits"],
                    "cache_misses": defended["cache_misses"],
                    "cache_miss_rate": defended["cache_miss_rate"],
                    "correlation_score": defended["correlation_score"],
                    "leakage_score": defended["leakage_score"],
                    "execution_time_ms": defended["execution_time_ms"],
                    "timing_variance": defended["timing_variance"],
                    "clock_cycles": defended["clock_cycles"],
                }
            )
            defended.update(defended_prediction)
            defended["leakage_reduction"] = round(before - defended["leakage_score"], 4)
            defended["label"] = "secure" if defended["leakage_score"] < before else sample["label"]
            defended["notes"] = defended["notes"] + [f"Defense activated: {technique}"]
            self.snapshot.defense_mode = True
            self.snapshot.defense_technique = technique
            self.snapshot.leakage_reduction = defended["leakage_reduction"]
            self.snapshot.ai_prediction = defended_prediction
            self._log(
                f"Auto-defense activated with {technique}; leakage {before:.2f} -> {defended['leakage_score']:.2f}."
            )
            return defended

        if self.snapshot.defense_mode:
            sample["defense_mode"] = True
            sample["defense_technique"] = self.snapshot.defense_technique
        return sample

    def _estimate_correlation(
        self,
        power_avg: float,
        power_variance: float,
        attack_type: str,
        defense_mode: bool,
        cache_miss_rate: float,
        timing_variance: float,
    ) -> float:
        attack_bonus = {"power": 0.26, "timing": 0.12, "cache": 0.18}.get(attack_type, 0.1)
        score = (
            (power_avg / 65)
            + (power_variance / 120)
            + (cache_miss_rate / 100)
            + timing_variance
            + attack_bonus
        )
        if defense_mode:
            score *= 0.72
        return round(clamp(score, 0.04, 0.98), 4)

    def _heuristic_prediction(self, sample: dict[str, Any]) -> dict[str, Any]:
        probability = clamp(
            (sample["leakage_score"] * 0.65)
            + (sample["correlation_score"] * 0.35),
            0.0,
            1.0,
        )
        return {
            "attack_probability": round(probability, 4),
            "risk_level": risk_level(probability),
            "model_confidence": round(0.65 + (probability * 0.25), 4),
            "top_features": self.predictor.top_features,
            "training_accuracy": self.predictor.training_accuracy,
        }

    async def _broadcast(self) -> None:
        if not self.subscribers:
            return
        frame = self.get_dashboard_frame()
        stale: list[asyncio.Queue] = []
        for queue in self.subscribers:
            if queue.full():
                stale.append(queue)
                continue
            await queue.put(frame)
        for queue in stale:
            self.subscribers.discard(queue)

    def _log(self, message: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.recent_logs.appendleft(f"[{timestamp}] {message}")
        self.snapshot.logs = list(self.recent_logs)
