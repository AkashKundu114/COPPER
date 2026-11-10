"""Neuromorphic Event-Driven Spike Anomaly Detector.

Implements Stage 13 Unified Observability Architecture:
- Emulates Leaky Integrate-and-Fire (LIF) biological neuron membrane dynamics for metric streams.
- Fires discrete diagnostic spikes when input current (metric surge) exceeds action potential threshold.
- Captures micro-second transient latency jitter and anomalous bursts missed by temporal averages.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnomalySpikeEvent:
    metric_name: str
    spike_timestamp_epoch: float
    membrane_potential: float
    threshold_exceeded: float
    urgency_level: str


class NeuromorphicAnomalySpiker:
    """Detects transient performance anomalies using Leaky Integrate-and-Fire (LIF) neuron dynamics."""

    def __init__(
        self,
        leak_factor: float = 0.85,
        firing_threshold: float = 100.0,
        resting_potential: float = 0.0,
    ) -> None:
        self.leak_factor = leak_factor
        self.firing_threshold = firing_threshold
        self.resting_potential = resting_potential
        self._membrane_potentials: dict[str, float] = {}
        self._spike_history: list[AnomalySpikeEvent] = []

    def integrate_reading(self, metric_name: str, input_stimulus: float) -> Optional[AnomalySpikeEvent]:
        """Integrate metric stimulus into membrane potential and check for action potential spike."""
        current_v = self._membrane_potentials.get(metric_name, self.resting_potential)

        # LIF Equation: V(t) = leak * V(t-1) + input_stimulus
        new_v = (current_v * self.leak_factor) + input_stimulus
        now = time.time()

        if new_v >= self.firing_threshold:
            # Action potential fires! Reset membrane potential
            self._membrane_potentials[metric_name] = self.resting_potential
            urgency = "CRITICAL" if new_v > self.firing_threshold * 1.5 else "HIGH"

            spike = AnomalySpikeEvent(
                metric_name=metric_name,
                spike_timestamp_epoch=now,
                membrane_potential=round(new_v, 2),
                threshold_exceeded=round(new_v - self.firing_threshold, 2),
                urgency_level=urgency,
            )
            self._spike_history.append(spike)
            return spike

        self._membrane_potentials[metric_name] = new_v
        return None

    def get_current_potential(self, metric_name: str) -> float:
        return self._membrane_potentials.get(metric_name, self.resting_potential)

    def get_spikes_count(self) -> int:
        return len(self._spike_history)
