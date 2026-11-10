"""Autonomous Telemetry-Driven Policy Self-Tuner.

Implements Stage 8 Configuration & Policy Management Architecture:
- Observes live telemetry metrics (P99 latency, error rates, queue backpressure).
- Computes optimal policy tuning adjustments (circuit thresholds, concurrency limits, batch sizes).
- Applies verified non-disruptive policy adjustments autonomously.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PolicyTuningRecommendation:
    parameter_name: str
    current_value: float
    recommended_value: float
    adjustment_reason: str
    confidence_score: float
    applied: bool = False


@dataclass
class SystemTelemetrySnapshot:
    p99_latency_ms: float
    error_rate: float
    queue_wait_ms: float
    gpu_vram_usage_gb: float
    active_requests_count: int


class AutonomousPolicyTuner:
    """Self-tuning optimization controller that adjusts operational parameters based on system telemetry."""

    def __init__(self) -> None:
        # Tunable knobs and their safe operational bounds
        self.tunable_knobs: dict[str, dict[str, float]] = {
            "max_batch_size": {"min": 1.0, "max": 32.0, "current": 8.0, "step": 1.0},
            "circuit_breaker_failure_threshold": {"min": 2.0, "max": 20.0, "current": 5.0, "step": 1.0},
            "inference_timeout_seconds": {"min": 5.0, "max": 120.0, "current": 30.0, "step": 5.0},
            "queue_worker_concurrency": {"min": 1.0, "max": 16.0, "current": 4.0, "step": 1.0},
        }
        self._tuning_history: list[PolicyTuningRecommendation] = []

    def evaluate_telemetry(self, snapshot: SystemTelemetrySnapshot) -> list[PolicyTuningRecommendation]:
        """Evaluate telemetry signals and generate targeted policy adjustments."""
        recommendations: list[PolicyTuningRecommendation] = []

        # Rule 1: High P99 latency or high queue wait -> decrease batch size or increase concurrency
        batch = self.tunable_knobs["max_batch_size"]
        if snapshot.p99_latency_ms > 500.0 or snapshot.queue_wait_ms > 200.0:
            if batch["current"] > batch["min"]:
                new_val = max(batch["min"], batch["current"] - 2.0)
                recommendations.append(
                    PolicyTuningRecommendation(
                        parameter_name="max_batch_size",
                        current_value=batch["current"],
                        recommended_value=new_val,
                        adjustment_reason=f"High latency ({snapshot.p99_latency_ms:.1f}ms): lowering batch size to reduce queue wait.",
                        confidence_score=0.88,
                    )
                )

        # Rule 2: Low latency and low queue wait with low VRAM -> increase batch size for higher throughput
        elif snapshot.p99_latency_ms < 100.0 and snapshot.gpu_vram_usage_gb < 6.0:
            if batch["current"] < batch["max"]:
                new_val = min(batch["max"], batch["current"] + 2.0)
                recommendations.append(
                    PolicyTuningRecommendation(
                        parameter_name="max_batch_size",
                        current_value=batch["current"],
                        recommended_value=new_val,
                        adjustment_reason="Low latency and ample VRAM headroom: expanding batch size for throughput.",
                        confidence_score=0.82,
                    )
                )

        # Rule 3: High error rate -> tighten circuit breaker failure threshold to isolate failures quickly
        cb = self.tunable_knobs["circuit_breaker_failure_threshold"]
        if snapshot.error_rate > 0.05:
            if cb["current"] > cb["min"]:
                new_val = max(cb["min"], cb["current"] - 1.0)
                recommendations.append(
                    PolicyTuningRecommendation(
                        parameter_name="circuit_breaker_failure_threshold",
                        current_value=cb["current"],
                        recommended_value=new_val,
                        adjustment_reason=f"Elevated error rate ({snapshot.error_rate:.1%}): tightening circuit trip threshold.",
                        confidence_score=0.92,
                    )
                )

        # Rule 4: High queue wait with low error rate -> increase worker concurrency if within bounds
        concur = self.tunable_knobs["queue_worker_concurrency"]
        if snapshot.queue_wait_ms > 150.0 and snapshot.error_rate < 0.02 and snapshot.gpu_vram_usage_gb < 7.0:
            if concur["current"] < concur["max"]:
                new_val = min(concur["max"], concur["current"] + 1.0)
                recommendations.append(
                    PolicyTuningRecommendation(
                        parameter_name="queue_worker_concurrency",
                        current_value=concur["current"],
                        recommended_value=new_val,
                        adjustment_reason="Queue wait pressure detected: scaling concurrency worker count.",
                        confidence_score=0.85,
                    )
                )

        return recommendations

    def apply_recommendation(self, rec: PolicyTuningRecommendation) -> bool:
        """Apply a validated tuning recommendation."""
        if rec.parameter_name not in self.tunable_knobs:
            return False

        knob = self.tunable_knobs[rec.parameter_name]
        clamped = max(knob["min"], min(knob["max"], rec.recommended_value))
        knob["current"] = clamped
        rec.applied = True
        self._tuning_history.append(rec)
        return True

    def get_parameter(self, param_name: str) -> float:
        return self.tunable_knobs[param_name]["current"]
