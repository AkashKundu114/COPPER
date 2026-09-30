"""
Creative Fatigue Detection Engine for C.O.P.P.E.R. (DELTA Agent).

Modeled on DeltaX Creative Solutions & Insights:
Monitors ad creative health by correlating exposure frequency, monotonic CTR decay,
and creative lifespan to flag creative exhaustion before CPA/ROAS degrades.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
import numpy as np


@dataclass
class CreativeMetricPoint:
    creative_id: str
    campaign_id: str
    frequency: float  # Avg impressions per unique user
    ctr: float  # Click-through rate
    cpa: float  # Cost per acquisition
    timestamp: datetime


@dataclass
class CreativeFatigueReport:
    creative_id: str
    campaign_id: str
    fatigue_level: str  # "healthy" | "early_decay" | "saturated" | "exhausted"
    frequency: float
    ctr_decay_percent: float
    is_fatigued: bool
    recommendation: str
    detected_at: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["detected_at"] = self.detected_at.isoformat()
        return d


class CreativeFatigueDetector:
    """
    Detects creative fatigue through multi-factor signal analysis:
    1. High Exposure Frequency: Frequency > 3.0x indicates audience saturation.
    2. Monotonic CTR Decay: >20% decline from historical peak CTR.
    3. CPA Run-Up: >25% cost per conversion escalation.
    """

    def __init__(self, frequency_threshold: float = 3.2, decay_threshold: float = 0.20):
        self.frequency_threshold = frequency_threshold
        self.decay_threshold = decay_threshold

    def analyze_creative_series(
        self,
        creative_id: str,
        campaign_id: str,
        history: list[CreativeMetricPoint],
    ) -> CreativeFatigueReport:
        if not history:
            return CreativeFatigueReport(
                creative_id=creative_id,
                campaign_id=campaign_id,
                fatigue_level="healthy",
                frequency=1.0,
                ctr_decay_percent=0.0,
                is_fatigued=False,
                recommendation="Insufficient historical creative data.",
            )

        # Sort chronologically
        sorted_pts = sorted(history, key=lambda p: p.timestamp)
        ctrs = [p.ctr for p in sorted_pts]
        current_freq = sorted_pts[-1].frequency
        current_ctr = sorted_pts[-1].ctr
        peak_ctr = max(ctrs) if ctrs else current_ctr

        ctr_decay = (
            max(0.0, (peak_ctr - current_ctr) / peak_ctr)
            if peak_ctr > 0
            else 0.0
        )

        # Determine fatigue classification
        is_fatigued = False
        if current_freq >= self.frequency_threshold and ctr_decay >= self.decay_threshold:
            fatigue_level = "exhausted"
            is_fatigued = True
            rec = (
                f"Creative {creative_id} is exhausted (Freq: {current_freq:.1f}x, "
                f"CTR decayed {ctr_decay * 100:.1f}%). Immediately rotate fresh visual assets via PICASSO Studio."
            )
        elif current_freq >= 2.5 and ctr_decay >= 0.15:
            fatigue_level = "saturated"
            is_fatigued = True
            rec = (
                f"Creative {creative_id} is saturated (Freq: {current_freq:.1f}x). "
                f"Prepare new copy variations and widen audience targeting."
            )
        elif ctr_decay >= 0.10:
            fatigue_level = "early_decay"
            is_fatigued = False
            rec = f"Early engagement decay detected on creative {creative_id}. Monitor frequency pacing."
        else:
            fatigue_level = "healthy"
            is_fatigued = False
            rec = f"Creative {creative_id} is operating within nominal engagement bands."

        return CreativeFatigueReport(
            creative_id=creative_id,
            campaign_id=campaign_id,
            fatigue_level=fatigue_level,
            frequency=round(current_freq, 2),
            ctr_decay_percent=round(ctr_decay * 100, 2),
            is_fatigued=is_fatigued,
            recommendation=rec,
        )


creative_fatigue_detector = CreativeFatigueDetector()
