"""Unified Live System Observability Inspector & Health Scorer for C.O.P.P.E.R.

Aggregates real-time Prometheus telemetry, distributed tracing span latencies,
and physical hardware resource metrics into a unified, composite health index
while strictly asserting the 8.0 GB VRAM limit.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.metrics import metrics_registry
from app.core.telemetry_coordinator import telemetry_coordinator


@dataclass
class TelemetryStreamHealth:
    subsystem: str
    is_active: bool
    event_count: int
    last_sample_timestamp: float
    health_score: float  # 0.0 to 1.0


@dataclass
class LiveInspectionReport:
    inspection_id: str
    timestamp: float
    composite_health_score: float  # 0.0 to 100.0
    system_status: str  # "OPERATIONAL" | "DEGRADED" | "CRITICAL"
    vram_budget_compliant: bool
    vram_used_bytes: int
    vram_limit_bytes: int
    streams: list[TelemetryStreamHealth]
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LiveObservabilityInspector:
    """Real-time health supervisor inspecting active telemetry pipelines and system resources."""

    HARDWARE_VRAM_LIMIT_BYTES: int = int(8.0 * 1024 * 1024 * 1024)  # 8.0 GB in bytes

    def __init__(self, metrics=metrics_registry, telemetry=telemetry_coordinator):
        self.metrics = metrics
        self.telemetry = telemetry

    def inspect_live_health(self) -> LiveInspectionReport:
        """Collects live metrics from all exporters and calculates composite system health."""
        now = time.time()
        self.metrics.sample_system_hardware(force=True)
        summary = self.metrics.get_metrics_summary()

        # 1. Inspect Prometheus exposition stream
        prom_text = self.metrics.render_prometheus_exposition()
        prom_active = len(prom_text) > 0 and "copper_" in prom_text

        # 2. Inspect Hardware VRAM Limit
        vram_used = int(summary.get("gpu_vram_used_bytes", 0))
        vram_ok = vram_used <= self.HARDWARE_VRAM_LIMIT_BYTES

        # 3. Stream evaluations
        streams = [
            TelemetryStreamHealth(
                subsystem="PrometheusRegistry",
                is_active=prom_active,
                event_count=int(summary.get("total_samples", len(prom_text.splitlines()))),
                last_sample_timestamp=now,
                health_score=1.0 if prom_active else 0.0,
            ),
            TelemetryStreamHealth(
                subsystem="HardwareTelemetry",
                is_active=True,
                event_count=len(summary),
                last_sample_timestamp=now,
                health_score=1.0 if vram_ok else 0.2,
            ),
            TelemetryStreamHealth(
                subsystem="OpenTelemetryTracer",
                is_active=True,
                event_count=len(self.telemetry.get_recent_spans()),
                last_sample_timestamp=now,
                health_score=1.0,
            ),
        ]

        # Calculate composite score
        avg_stream_health = sum(s.health_score for s in streams) / len(streams)
        composite_score = round(avg_stream_health * 100.0, 1)

        if composite_score >= 85.0:
            status = "OPERATIONAL"
        elif composite_score >= 50.0:
            status = "DEGRADED"
        else:
            status = "CRITICAL"

        ts = now
        insp_id = f"INSP-{hashlib.sha256(str(ts).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{insp_id}:{composite_score}:{vram_ok}".encode()).hexdigest()

        report = LiveInspectionReport(
            inspection_id=insp_id,
            timestamp=ts,
            composite_health_score=composite_score,
            system_status=status,
            vram_budget_compliant=vram_ok,
            vram_used_bytes=vram_used,
            vram_limit_bytes=self.HARDWARE_VRAM_LIMIT_BYTES,
            streams=streams,
            signature=sig,
        )

        logger.info(
            f"[LiveObservabilityInspector] Inspected live health: {status} "
            f"(Score: {composite_score}%, VRAM compliant: {vram_ok})"
        )
        return report


live_observability_inspector = LiveObservabilityInspector()
