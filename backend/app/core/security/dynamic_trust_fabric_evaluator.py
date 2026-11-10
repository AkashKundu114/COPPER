"""Continuous Zero-Trust Dynamic Trust Fabric and Subagent Behavioral Evaluator.

Implements Stage 13 Zero-Trust Security Architecture:
- Evaluates real-time multidimensional trust scores (0.0 to 1.0) for executing subagents.
- Monitors behavioral anomalies: unexpected tool calls, rate limit breaches, and token spikes.
- Dynamically demotes permission tiers or revokes access keys when trust scores fall below safe thresholds.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TrustTier(str, Enum):
    TRUSTED = "TRUSTED"           # Score >= 0.80: Full privileged access
    PROBATIONARY = "PROBATIONARY" # Score 0.50 - 0.79: Standard read/write with auditing
    RESTRICTED = "RESTRICTED"     # Score 0.30 - 0.49: Read-only safe tools
    REVOKED = "REVOKED"           # Score < 0.30: Immediate access isolation


@dataclass
class SubagentTrustProfile:
    agent_id: str
    current_trust_score: float
    trust_tier: TrustTier
    violations_count: int
    last_evaluated_epoch: float
    is_isolated: bool


@dataclass
class TrustEvaluationResult:
    agent_id: str
    previous_score: float
    new_score: float
    assigned_tier: TrustTier
    demoted: bool
    reasons: list[str]


class DynamicTrustFabricEvaluator:
    """Manages continuous behavioral trust scoring and dynamic authorization adjustments."""

    def __init__(self, initial_trust_score: float = 0.90) -> None:
        self.initial_trust_score = initial_trust_score
        self._profiles: dict[str, SubagentTrustProfile] = {}

    def get_or_create_profile(self, agent_id: str) -> SubagentTrustProfile:
        if agent_id not in self._profiles:
            self._profiles[agent_id] = SubagentTrustProfile(
                agent_id=agent_id,
                current_trust_score=self.initial_trust_score,
                trust_tier=TrustTier.TRUSTED,
                violations_count=0,
                last_evaluated_epoch=time.time(),
                is_isolated=False,
            )
        return self._profiles[agent_id]

    def record_behavioral_signal(
        self,
        agent_id: str,
        signal_type: str,  # "TOOL_SUCCESS", "RATE_LIMIT_HIT", "UNAUTHORIZED_PROBE", "TOKEN_SPIKE"
    ) -> TrustEvaluationResult:
        """Adjust trust score according to observed behavioral signal."""
        profile = self.get_or_create_profile(agent_id)
        prev_score = profile.current_trust_score
        reasons = []

        # Penalties and rewards
        if signal_type == "TOOL_SUCCESS":
            delta = 0.02
            reasons.append("Verified nominal tool execution.")
        elif signal_type == "RATE_LIMIT_HIT":
            delta = -0.15
            profile.violations_count += 1
            reasons.append("Rate limit threshold breached.")
        elif signal_type == "UNAUTHORIZED_PROBE":
            delta = -0.35
            profile.violations_count += 1
            reasons.append("Attempted invocation of unauthorized resource.")
        elif signal_type == "TOKEN_SPIKE":
            delta = -0.10
            reasons.append("Unusual generation token spike observed.")
        else:
            delta = 0.0

        new_score = max(0.0, min(1.0, prev_score + delta))
        profile.current_trust_score = round(new_score, 2)
        profile.last_evaluated_epoch = time.time()

        # Update Tier
        if new_score >= 0.80:
            new_tier = TrustTier.TRUSTED
        elif new_score >= 0.50:
            new_tier = TrustTier.PROBATIONARY
        elif new_score >= 0.30:
            new_tier = TrustTier.RESTRICTED
        else:
            new_tier = TrustTier.REVOKED
            profile.is_isolated = True

        demoted = new_score < prev_score and new_tier != profile.trust_tier
        profile.trust_tier = new_tier

        return TrustEvaluationResult(
            agent_id=agent_id,
            previous_score=prev_score,
            new_score=profile.current_trust_score,
            assigned_tier=new_tier,
            demoted=demoted,
            reasons=reasons,
        )
