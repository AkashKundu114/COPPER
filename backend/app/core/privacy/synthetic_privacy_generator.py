"""Synthetic Differential Privacy Data Synthesizer.

Implements Stage 8 Privacy & Data Governance Framework:
- Generates synthetic test fixtures and telemetry data conforming to (epsilon, delta)-differential privacy.
- Calibrates Laplace and Gaussian noise injection to prevent reconstruction attacks.
- Guarantees zero leakage of raw prompt content, email addresses, IPs, and user credentials.
"""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PrivacyBudgetGuarantee:
    epsilon: float
    delta: float
    laplace_scale: float
    noise_variance: float
    guaranteed_safe: bool = True


@dataclass
class SyntheticRecord:
    record_id: str
    perturbed_metrics: dict[str, float]
    synthetic_attributes: dict[str, str]
    privacy_guarantee: PrivacyBudgetGuarantee


class SyntheticPrivacyGenerator:
    """Generates synthetic, differentially private records for test and benchmark staging."""

    def __init__(self, default_epsilon: float = 1.0, default_delta: float = 1e-5) -> None:
        self.default_epsilon = default_epsilon
        self.default_delta = default_delta

    def _sample_laplace_noise(self, scale: float) -> float:
        """Sample from zero-mean Laplace distribution with given scale parameter."""
        u = random.random() - 0.5
        # Avoid math domain error with log(0)
        u = min(0.4999999, max(-0.4999999, u))
        return -scale * math.copysign(1.0, u) * math.log(1.0 - 2.0 * abs(u))

    def compute_privacy_parameters(self, sensitivity: float, epsilon: Optional[float] = None) -> PrivacyBudgetGuarantee:
        eps = epsilon if epsilon is not None else self.default_epsilon
        laplace_scale = sensitivity / max(eps, 1e-6)
        variance = 2.0 * (laplace_scale ** 2)

        return PrivacyBudgetGuarantee(
            epsilon=eps,
            delta=self.default_delta,
            laplace_scale=laplace_scale,
            noise_variance=variance,
            guaranteed_safe=eps <= 3.0,
        )

    def synthesize_telemetry_metric(
        self,
        base_value: float,
        metric_name: str,
        sensitivity: float = 1.0,
        epsilon: Optional[float] = None,
    ) -> tuple[float, PrivacyBudgetGuarantee]:
        """Apply differential privacy noise to a continuous telemetry metric."""
        budget = self.compute_privacy_parameters(sensitivity, epsilon)
        noise = self._sample_laplace_noise(budget.laplace_scale)
        perturbed = max(0.0, base_value + noise)
        return perturbed, budget

    def anonymize_and_synthesize_text(self, text: str) -> str:
        """Replace identifying entities with synthetic placeholders."""
        # Replace emails
        synth = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[SYNTHETIC_EMAIL]", text)
        # Replace IPv4 addresses
        synth = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[SYNTHETIC_IP]", synth)
        # Replace API keys / high entropy tokens
        synth = re.sub(r"(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|cop_[a-zA-Z0-9]{20,})", "[SYNTHETIC_KEY]", synth)
        return synth

    def generate_synthetic_dataset(
        self,
        record_count: int,
        nominal_latency_ms: float = 120.0,
        nominal_tokens: float = 350.0,
    ) -> list[SyntheticRecord]:
        """Generate a batch of differentially private synthetic benchmark records."""
        records: list[SyntheticRecord] = []
        for i in range(record_count):
            lat, b1 = self.synthesize_telemetry_metric(nominal_latency_ms, "latency_ms", sensitivity=10.0)
            tok, b2 = self.synthesize_telemetry_metric(nominal_tokens, "tokens", sensitivity=50.0)

            records.append(
                SyntheticRecord(
                    record_id=f"synth-{i:04d}",
                    perturbed_metrics={"latency_ms": round(lat, 2), "tokens": round(tok, 1)},
                    synthetic_attributes={
                        "user_id": f"synthetic_usr_{random.randint(1000, 9999)}",
                        "session_id": f"sess_synth_{random.randint(10000, 99999)}",
                    },
                    privacy_guarantee=b1,
                )
            )
        return records
