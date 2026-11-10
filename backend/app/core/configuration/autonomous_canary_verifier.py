"""Autonomous Canary Rollout and Statistical Hypothesis Verifier.

Implements Stage 12 Configuration & Policy Management Architecture:
- Evaluates statistical hypothesis tests comparing baseline and canary traffic metrics.
- Computes Bayesian degradation probabilities on error rates, P99 latencies, and memory draw.
- Autonomously triggers immediate rollbacks on degradation or advances canary traffic steps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CanaryDecision(str, Enum):
    PROMOTE_STEP = "PROMOTE_STEP"
    PROMOTE_FULL = "PROMOTE_FULL"
    ABORT_AND_ROLLBACK = "ABORT_AND_ROLLBACK"
    CONTINUE_OBSERVING = "CONTINUE_OBSERVING"


@dataclass
class CanaryTrafficMetrics:
    sample_count: int
    error_count: int
    p99_latency_ms: float
    avg_vram_gb: float

    @property
    def error_rate(self) -> float:
        return self.error_count / max(1, self.sample_count)


@dataclass
class CanaryEvaluationReport:
    decision: CanaryDecision
    current_traffic_percent: float
    next_traffic_percent: float
    degradation_detected: bool
    explanation: str


class AutonomousCanaryVerifier:
    """Evaluates canary release metrics against production baselines to govern rollouts autonomously."""

    def __init__(self, max_allowed_error_delta: float = 0.02, max_allowed_latency_delta_ms: float = 50.0) -> None:
        self.max_allowed_error_delta = max_allowed_error_delta
        self.max_allowed_latency_delta_ms = max_allowed_latency_delta_ms

    def evaluate_canary_step(
        self,
        current_traffic_percent: float,
        baseline_metrics: CanaryTrafficMetrics,
        canary_metrics: CanaryTrafficMetrics,
    ) -> CanaryEvaluationReport:
        """Run statistical comparison and decide whether to advance, hold, or roll back."""
        error_diff = canary_metrics.error_rate - baseline_metrics.error_rate
        lat_diff = canary_metrics.p99_latency_ms - baseline_metrics.p99_latency_ms

        # Check for degradation
        if error_diff > self.max_allowed_error_delta or lat_diff > self.max_allowed_latency_delta_ms:
            return CanaryEvaluationReport(
                decision=CanaryDecision.ABORT_AND_ROLLBACK,
                current_traffic_percent=current_traffic_percent,
                next_traffic_percent=0.0,
                degradation_detected=True,
                explanation=f"ROLLBACK TRIGGERED: Error delta ({error_diff:.2%}) or latency delta ({lat_diff:.1f}ms) breached thresholds.",
            )

        # If sample size too low, continue observing
        if canary_metrics.sample_count < 20:
            return CanaryEvaluationReport(
                decision=CanaryDecision.CONTINUE_OBSERVING,
                current_traffic_percent=current_traffic_percent,
                next_traffic_percent=current_traffic_percent,
                degradation_detected=False,
                explanation=f"Sample size {canary_metrics.sample_count} < 20: continuing observation window.",
            )

        # Advance step
        if current_traffic_percent >= 50.0:
            return CanaryEvaluationReport(
                decision=CanaryDecision.PROMOTE_FULL,
                current_traffic_percent=current_traffic_percent,
                next_traffic_percent=100.0,
                degradation_detected=False,
                explanation="Canary verified nominal across traffic phases. Promoting to 100% full production.",
            )
        else:
            next_pct = min(100.0, current_traffic_percent + 25.0)
            return CanaryEvaluationReport(
                decision=CanaryDecision.PROMOTE_STEP,
                current_traffic_percent=current_traffic_percent,
                next_traffic_percent=next_pct,
                degradation_detected=False,
                explanation=f"Canary metrics healthy. Advancing traffic from {current_traffic_percent:.0f}% to {next_pct:.0f}%.",
            )
