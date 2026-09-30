"""
Multi-Touch Attribution (MTA) Engine for C.O.P.P.E.R. (DELTA Agent).

Modeled on DeltaX Measurement & Attribution:
Calculates cross-channel attribution credit across multi-point conversion paths
using Linear, Time-Decay, and Game-Theoretic Shapley Value models.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import itertools
import math
from typing import Any


@dataclass
class Touchpoint:
    channel: str  # "search", "social", "display", "retargeting", "email"
    campaign_id: str
    timestamp: datetime


@dataclass
class ConversionJourney:
    journey_id: str
    touchpoints: list[Touchpoint]
    conversion_value: float
    converted_at: datetime


class MultiTouchAttributionEngine:
    """
    Computes fair marketing channel contribution across multi-touch customer paths.
    """

    @staticmethod
    def linear_attribution(journeys: list[ConversionJourney]) -> dict[str, float]:
        """Distributes conversion credit equally across all touchpoints in a journey."""
        scores: dict[str, float] = {}
        for j in journeys:
            if not j.touchpoints:
                continue
            split_credit = j.conversion_value / len(j.touchpoints)
            for tp in j.touchpoints:
                scores[tp.channel] = scores.get(tp.channel, 0.0) + split_credit
        return {k: round(v, 2) for k, v in scores.items()}

    @staticmethod
    def time_decay_attribution(
        journeys: list[ConversionJourney], half_life_days: float = 7.0
    ) -> dict[str, float]:
        """
        Exponentially weights touchpoints closer to the conversion moment.
        Credit decays with a specified half-life (default 7 days).
        """
        scores: dict[str, float] = {}
        half_life_seconds = half_life_days * 86400.0

        for j in journeys:
            if not j.touchpoints:
                continue

            weights = []
            for tp in j.touchpoints:
                delta_sec = max(0.0, (j.converted_at - tp.timestamp).total_seconds())
                # Exponential decay formula: 2^(-delta / half_life)
                weight = math.pow(2.0, -delta_sec / max(1.0, half_life_seconds))
                weights.append(weight)

            total_weight = sum(weights) or 1.0
            for tp, w in zip(j.touchpoints, weights):
                credit = (w / total_weight) * j.conversion_value
                scores[tp.channel] = scores.get(tp.channel, 0.0) + credit

        return {k: round(v, 2) for k, v in scores.items()}

    @staticmethod
    def shapley_value_attribution(journeys: list[ConversionJourney]) -> dict[str, float]:
        """
        Game-Theoretic Shapley Value Attribution.
        Computes marginal contributions across all channel coalition subsets:
        phi_i = sum( (|S|! * (|N| - |S| - 1)! / |N|!) * [v(S U {i}) - v(S)] )
        """
        # Collect unique channels
        channels = set()
        for j in journeys:
            for tp in j.touchpoints:
                channels.add(tp.channel)

        channel_list = sorted(list(channels))
        n = len(channel_list)
        if n == 0:
            return {}
        if n == 1:
            total_val = sum(j.conversion_value for j in journeys)
            return {channel_list[0]: round(total_val, 2)}

        # Characteristic function v(S) evaluates conversion value achieved by channel set S
        def coalition_value(coalition: frozenset[str]) -> float:
            val = 0.0
            for j in journeys:
                j_channels = {tp.channel for tp in j.touchpoints}
                # If all touchpoints in this journey belong to the coalition, credit is counted
                if j_channels.issubset(coalition):
                    val += j.conversion_value
            return val

        shapley_scores: dict[str, float] = {ch: 0.0 for ch in channel_list}

        for i in channel_list:
            other_players = [ch for ch in channel_list if ch != i]
            for r in range(len(other_players) + 1):
                for subset in itertools.combinations(other_players, r):
                    S = frozenset(subset)
                    S_with_i = S | frozenset([i])
                    marginal = coalition_value(S_with_i) - coalition_value(S)
                    cardinality_S = len(S)
                    # Shapley weight
                    weight = (
                        math.factorial(cardinality_S)
                        * math.factorial(n - cardinality_S - 1)
                    ) / math.factorial(n)
                    shapley_scores[i] += weight * marginal

        return {k: round(v, 2) for k, v in shapley_scores.items()}


mta_engine = MultiTouchAttributionEngine()
