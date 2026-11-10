"""Carbon Footprint and Scope 2 Emissions FinOps Tracker.

Implements Stage 10 Cost & Resource Governance Architecture:
- Tracks Scope 2 greenhouse gas emissions (gCO2e, kgCO2e) derived from GPU/CPU electrical consumption.
- Models regional grid emission intensities (e.g. gCO2e per kWh).
- Calculates sustainability metrics: grams of CO2e per 1K generated tokens and carbon offset quotas.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CarbonEmissionRecord:
    batch_id: str
    tokens_generated: int
    kwh_consumed: float
    grid_emission_factor_g_per_kwh: float
    carbon_emissions_grams_co2e: float
    grams_co2e_per_1k_tokens: float
    timestamp_epoch: float = field(default_factory=time.time)


class CarbonFootprintTracker:
    """Calculates greenhouse gas emissions and environmental sustainability metrics for inference."""

    # Standard regional grid emission intensities (grams CO2e per kWh)
    GRID_INTENSITIES: dict[str, float] = {
        "global_average": 475.0,
        "us_average": 380.0,
        "eu_average": 255.0,
        "clean_hydro_nuclear": 50.0,
        "coal_heavy": 820.0,
    }

    def __init__(self, default_region: str = "us_average") -> None:
        self.default_region = default_region
        self.emission_factor = self.GRID_INTENSITIES.get(default_region, 380.0)
        self._emission_history: list[CarbonEmissionRecord] = []

    def record_inference_emissions(
        self,
        batch_id: str,
        tokens_generated: int,
        kwh_consumed: float,
        region: Optional[str] = None,
    ) -> CarbonEmissionRecord:
        """Calculate and log carbon emissions for an executed inference batch."""
        factor = self.GRID_INTENSITIES.get(region or self.default_region, self.emission_factor)

        # Emissions (g CO2e) = kWh * factor
        total_g_co2e = kwh_consumed * factor
        g_per_1k = (total_g_co2e / max(1, tokens_generated)) * 1000.0

        record = CarbonEmissionRecord(
            batch_id=batch_id,
            tokens_generated=tokens_generated,
            kwh_consumed=kwh_consumed,
            grid_emission_factor_g_per_kwh=factor,
            carbon_emissions_grams_co2e=round(total_g_co2e, 4),
            grams_co2e_per_1k_tokens=round(g_per_1k, 4),
        )
        self._emission_history.append(record)
        return record

    def get_aggregate_footprint(self) -> dict[str, float]:
        """Aggregate total emissions and sustainability metrics."""
        total_kwh = sum(r.kwh_consumed for r in self._emission_history)
        total_g_co2 = sum(r.carbon_emissions_grams_co2e for r in self._emission_history)
        total_tokens = sum(r.tokens_generated for r in self._emission_history)

        avg_g_per_1k = (total_g_co2 / max(1, total_tokens)) * 1000.0 if total_tokens > 0 else 0.0

        return {
            "total_batches_profiled": len(self._emission_history),
            "total_tokens_generated": total_tokens,
            "total_kwh_consumed": round(total_kwh, 6),
            "total_grams_co2e": round(total_g_co2, 4),
            "total_kg_co2e": round(total_g_co2 / 1000.0, 6),
            "avg_grams_co2e_per_1k_tokens": round(avg_g_per_1k, 4),
        }
