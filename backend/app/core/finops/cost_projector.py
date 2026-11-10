"""Predictive FinOps Cost & Resource Consumption Projector for C.O.P.P.E.R.

Projects 30-day storage growth, token expenditure, and computes cost savings of
local-first inference relative to commercial cloud API equivalents, enforcing
strict hardware runway against the 8.0 GB VRAM limit.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.finops.ledger import ResourceAccountingLedger, resource_ledger
from app.core.finops.storage_sentinel import StorageQuotaSentinel, storage_quota_sentinel
from app.core.logger import logger


@dataclass
class StorageProjection:
    current_storage_mb: float
    projected_30_day_storage_mb: float
    quota_limit_mb: float
    quota_exhaustion_days: float | None
    will_exceed_quota: bool


@dataclass
class TokenCostProjection:
    tokens_past_period: int
    projected_30_day_tokens: int
    local_cost_usd: float  # $0.0 for local-first
    equivalent_cloud_cost_usd: float  # Estimated at $5.00 / 1M tokens equivalent
    projected_monthly_savings_usd: float


@dataclass
class FinOpsProjectionReport:
    report_id: str
    timestamp: float
    hardware_vram_limit_gb: float
    peak_vram_observed_gb: float
    vram_safe: bool
    storage_projection: StorageProjection
    token_cost_projection: TokenCostProjection
    projection_healthy: bool
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FinOpsCostProjector:
    """Calculates forward-looking resource growth and cloud cost avoidance metrics."""

    CLOUD_EQUIVALENT_PRICE_PER_M_TOKENS: float = 5.00  # $5.00 per 1M blended tokens
    HARDWARE_VRAM_CEILING_GB: float = 8.0

    def __init__(
        self,
        ledger: ResourceAccountingLedger | None = None,
        storage_sentinel: StorageQuotaSentinel | None = None,
    ):
        self.ledger = ledger or resource_ledger
        self.storage_sentinel = storage_sentinel or storage_quota_sentinel

    def project_storage_growth(self, daily_growth_rate_mb: float = 5.0) -> StorageProjection:
        """Projects storage usage over a 30-day window based on disk sentinel status."""
        status = self.storage_sentinel.evaluate_storage_quota()
        current_mb = status.total_used_mb
        quota_mb = status.quota_limit_mb

        projected_30d = current_mb + (daily_growth_rate_mb * 30.0)
        will_exceed = projected_30d >= quota_mb

        days_remaining = None
        if daily_growth_rate_mb > 0:
            free_mb = max(0.0, quota_mb - current_mb)
            days_remaining = round(free_mb / daily_growth_rate_mb, 1)

        return StorageProjection(
            current_storage_mb=round(current_mb, 2),
            projected_30_day_storage_mb=round(projected_30d, 2),
            quota_limit_mb=round(quota_mb, 2),
            quota_exhaustion_days=days_remaining,
            will_exceed_quota=will_exceed,
        )

    def project_token_costs(self, sample_period_days: float = 1.0) -> TokenCostProjection:
        """Projects token expenditure and calculates commercial cloud cost avoidance."""
        summary = self.ledger.get_global_summary()
        tokens_total = summary.get("total_tokens", 0)

        # Baseline projection: assume measured tokens scale linearly to 30 days
        daily_tokens = (tokens_total / max(sample_period_days, 0.1)) if tokens_total > 0 else 10000
        projected_30d_tokens = int(daily_tokens * 30)

        local_cost = 0.0  # Local inference is free of API charges
        equiv_cloud_cost = (projected_30d_tokens / 1_000_000.0) * self.CLOUD_EQUIVALENT_PRICE_PER_M_TOKENS
        savings = equiv_cloud_cost - local_cost

        return TokenCostProjection(
            tokens_past_period=tokens_total,
            projected_30_day_tokens=projected_30d_tokens,
            local_cost_usd=round(local_cost, 2),
            equivalent_cloud_cost_usd=round(equiv_cloud_cost, 2),
            projected_monthly_savings_usd=round(savings, 2),
        )

    def generate_projection_report(self) -> FinOpsProjectionReport:
        """Generates unified 30-day FinOps projection report."""
        storage_proj = self.project_storage_growth()
        token_proj = self.project_token_costs()

        # VRAM safety check
        summary = self.ledger.get_global_summary()
        peak_vram_bytes = summary.get("peak_vram_bytes", 0)
        peak_vram_gb = peak_vram_bytes / (1024.0 ** 3)
        vram_safe = peak_vram_gb <= self.HARDWARE_VRAM_CEILING_GB

        healthy = (not storage_proj.will_exceed_quota) and vram_safe

        ts = time.time()
        report_id = f"FINOPS-PROJ-{hashlib.sha256(str(ts).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{report_id}:{healthy}:{token_proj.projected_monthly_savings_usd}".encode()).hexdigest()

        report = FinOpsProjectionReport(
            report_id=report_id,
            timestamp=ts,
            hardware_vram_limit_gb=self.HARDWARE_VRAM_CEILING_GB,
            peak_vram_observed_gb=round(peak_vram_gb, 2),
            vram_safe=vram_safe,
            storage_projection=storage_proj,
            token_cost_projection=token_proj,
            projection_healthy=healthy,
            signature=sig,
        )

        logger.info(
            f"[FinOpsCostProjector] Generated projection: {report_id} "
            f"(VRAM Safe={vram_safe}, 30d Savings=${token_proj.projected_monthly_savings_usd}, Healthy={healthy})"
        )
        return report


finops_cost_projector = FinOpsCostProjector()
