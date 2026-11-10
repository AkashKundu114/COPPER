"""AIOps Predictive Anomaly Detector and Dynamic Adaptive Telemetry Sampler.

Implements Stage 8 Observability Architecture:
- Tracks latency, token generation speed, and queue depth time series.
- Detects anomalies using robust statistical sliding windows (Z-score / IQR).
- Dynamically increases sampling frequency upon anomaly detection to capture full-fidelity traces.
- Emits predictive warnings before SLA thresholds are violated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AnomalyDetectionResult:
    is_anomaly: bool
    metric_name: str
    observed_value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    recommended_sampling_rate: float
    prediction_summary: str


class AIOpsAnomalyPredictor:
    """Predictive AIOps engine for performance anomaly detection and adaptive sampling."""

    def __init__(
        self,
        window_size: int = 50,
        z_threshold: float = 2.5,
        base_sampling_rate: float = 0.1,
        max_sampling_rate: float = 1.0,
    ) -> None:
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.base_sampling_rate = base_sampling_rate
        self.max_sampling_rate = max_sampling_rate
        self._metric_history: dict[str, list[float]] = {}
        self._current_sampling_rates: dict[str, float] = {}

    def record_metric(self, metric_name: str, value: float) -> AnomalyDetectionResult:
        """Record an observed metric value and evaluate for statistical anomaly."""
        if metric_name not in self._metric_history:
            self._metric_history[metric_name] = []
            self._current_sampling_rates[metric_name] = self.base_sampling_rate

        history = self._metric_history[metric_name]
        history.append(value)
        if len(history) > self.window_size:
            history.pop(0)

        # Baseline calculation
        if len(history) < 5:
            return AnomalyDetectionResult(
                is_anomaly=False,
                metric_name=metric_name,
                observed_value=value,
                baseline_mean=value,
                baseline_std=0.0,
                z_score=0.0,
                recommended_sampling_rate=self.base_sampling_rate,
                prediction_summary="Warmup phase: baseline forming.",
            )

        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = math.sqrt(variance) if variance > 1e-9 else 1e-6

        z_score = abs(value - mean) / std
        is_anomaly = z_score >= self.z_threshold

        if is_anomaly:
            # Step up sampling rate to maximum to capture full diagnostic detail
            sampling_rate = self.max_sampling_rate
            summary = f"ANOMALY DETECTED: {metric_name}={value:.2f} (Z={z_score:.2f} > {self.z_threshold}). Full trace sampling triggered."
        else:
            # Gradual decay towards base sampling rate
            current = self._current_sampling_rates.get(metric_name, self.base_sampling_rate)
            sampling_rate = max(self.base_sampling_rate, current * 0.95)
            summary = f"Nominal: {metric_name}={value:.2f} (Z={z_score:.2f}). Adaptive sampling at {sampling_rate:.2%}."

        self._current_sampling_rates[metric_name] = sampling_rate

        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            metric_name=metric_name,
            observed_value=value,
            baseline_mean=mean,
            baseline_std=std,
            z_score=z_score,
            recommended_sampling_rate=sampling_rate,
            prediction_summary=summary,
        )

    def get_effective_sampling_rate(self, metric_name: str) -> float:
        return self._current_sampling_rates.get(metric_name, self.base_sampling_rate)

    def predict_sla_breach(self, metric_name: str, threshold: float) -> tuple[bool, float]:
        """Predict whether metric trend threatens an impending SLA breach."""
        history = self._metric_history.get(metric_name, [])
        if len(history) < 5:
            return False, 0.0

        # Simple linear trend estimation over recent measurements
        recent = history[-5:]
        delta = (recent[-1] - recent[0]) / len(recent)
        projected = recent[-1] + delta * 3  # project 3 steps ahead

        threatened = projected >= threshold
        confidence = min(1.0, max(0.0, projected / max(threshold, 1e-6)))
        return threatened, confidence
