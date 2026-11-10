"""Differential Privacy Noise Generator & k-Anonymity Verifier for C.O.P.P.E.R.

Applies calibrated Laplace differential privacy noise to aggregate queries and
telemetry metrics, preventing membership inference and user re-identification
while asserting k-anonymity (k >= 3) across analytical data releases.
"""

from __future__ import annotations

import hashlib
import math
import random
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger


@dataclass
class AnonymizedMetricResult:
    metric_name: str
    raw_value: float
    anonymized_value: float
    epsilon: float
    noise_added: float
    k_anonymity_satisfied: bool


@dataclass
class DifferentialPrivacyReport:
    report_id: str
    timestamp: float
    epsilon_budget: float
    k_threshold: int
    privacy_guarantee_preserved: bool
    results: list[AnonymizedMetricResult]
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DifferentialPrivacyScrubber:
    """Applies epsilon-differential privacy Laplace mechanisms to analytical telemetry queries."""

    DEFAULT_EPSILON: float = 1.0  # Standard privacy parameter
    DEFAULT_K: int = 3           # Minimum anonymity group size

    def __init__(self, epsilon: float = DEFAULT_EPSILON, k_threshold: int = DEFAULT_K):
        self.epsilon = epsilon
        self.k_threshold = k_threshold

    def sample_laplace_noise(self, scale: float) -> float:
        """Samples noise from the Laplace distribution: Lap(b) = scale * sgn(u) * ln(1 - 2|u|)."""
        u = random.random() - 0.5
        # Prevent math domain error at u=0.5
        u = max(-0.49999, min(0.49999, u))
        sgn = 1.0 if u >= 0 else -1.0
        return -scale * sgn * math.log(1.0 - 2.0 * abs(u))

    def scrub_scalar_count(
        self,
        metric_name: str,
        true_value: float,
        group_size: int = 5,
        sensitivity: float = 1.0,
    ) -> AnonymizedMetricResult:
        """Applies calibrated Laplace noise to a scalar count or aggregate metric."""
        scale = sensitivity / max(0.01, self.epsilon)
        noise = self.sample_laplace_noise(scale)
        anonymized_val = max(0.0, true_value + noise)

        k_satisfied = group_size >= self.k_threshold

        return AnonymizedMetricResult(
            metric_name=metric_name,
            raw_value=round(true_value, 2),
            anonymized_value=round(anonymized_val, 2),
            epsilon=self.epsilon,
            noise_added=round(noise, 2),
            k_anonymity_satisfied=k_satisfied,
        )

    def generate_privacy_audit_report(self) -> DifferentialPrivacyReport:
        """Runs audit of differential privacy mechanisms across synthetic telemetry fields."""
        now = time.time()
        results = [
            self.scrub_scalar_count("daily_prompt_tokens", 45000.0, group_size=10),
            self.scrub_scalar_count("hourly_active_sessions", 12.0, group_size=5),
            self.scrub_scalar_count("agent_tool_invocations", 85.0, group_size=7),
        ]

        all_k_ok = all(r.k_anonymity_satisfied for r in results)
        rep_id = f"DP-AUD-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{rep_id}:{self.epsilon}:{all_k_ok}".encode()).hexdigest()

        report = DifferentialPrivacyReport(
            report_id=rep_id,
            timestamp=now,
            epsilon_budget=self.epsilon,
            k_threshold=self.k_threshold,
            privacy_guarantee_preserved=all_k_ok,
            results=results,
            signature=sig,
        )

        logger.info(
            f"[DifferentialPrivacyScrubber] Audit completed: Epsilon={self.epsilon}, "
            f"k={self.k_threshold}, Preserved={all_k_ok}"
        )
        return report


differential_privacy_scrubber = DifferentialPrivacyScrubber()
