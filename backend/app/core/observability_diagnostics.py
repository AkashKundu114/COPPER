"""Unified System Observability Diagnostics & Health Verifier for C.O.P.P.E.R.

Executes comprehensive end-to-end health audits across telemetry exporters,
Prometheus metrics registries, distributed tracing contexts, and hardware utilization limits.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.metrics import metrics_registry
from app.core.telemetry_coordinator import telemetry_coordinator


@dataclass
class SubsystemDiagnostic:
    name: str
    status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    latency_ms: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservabilityHealthReport:
    generated_at: float
    overall_status: str
    vram_budget_compliant: bool
    diagnostics: list[SubsystemDiagnostic] = field(default_factory=list)


class ObservabilityDiagnosticsEngine:
    """Diagnoses platform telemetry, hardware utilization, and tracing health."""

    def __init__(self, metrics=metrics_registry, telemetry=telemetry_coordinator):
        self.metrics = metrics
        self.telemetry = telemetry

    async def run_diagnostics(self) -> ObservabilityHealthReport:
        """Executes full diagnostic suite across telemetry components."""
        start_ts = time.time()
        subsystems: list[SubsystemDiagnostic] = []

        # 1. Prometheus Registry Probe
        t0 = time.time()
        exported = self.metrics.render_prometheus_exposition()
        prom_latency = (time.time() - t0) * 1000.0
        subsystems.append(
            SubsystemDiagnostic(
                name="PrometheusMetricsRegistry",
                status="HEALTHY" if "copper_" in exported else "DEGRADED",
                latency_ms=round(prom_latency, 2),
                details={"metrics_bytes": len(exported)},
            )
        )

        # 2. Hardware Resource & 8GB VRAM Compliance Probe
        t1 = time.time()
        vram_bytes = self.metrics.vram_used_bytes.get()
        vram_gb = vram_bytes / (1024.0 * 1024.0 * 1024.0)
        vram_compliant = vram_gb <= 8.0
        hw_latency = (time.time() - t1) * 1000.0
        
        hw_status = "HEALTHY" if vram_compliant else "CRITICAL"
        subsystems.append(
            SubsystemDiagnostic(
                name="HardwareTelemetrySentinel",
                status=hw_status,
                latency_ms=round(hw_latency, 2),
                details={
                    "vram_used_gb": round(vram_gb, 2),
                    "vram_ceiling_gb": 8.0,
                    "compliant": vram_compliant,
                },
            )
        )

        # 3. Distributed Tracing Context Probe
        t2 = time.time()
        async with self.telemetry.start_span("diagnostic_health_probe") as span:
            span.add_event("probe_event", {"purpose": "health_check"})
        trace_latency = (time.time() - t2) * 1000.0
        
        recent_spans = self.telemetry.get_recent_spans(limit=5)
        subsystems.append(
            SubsystemDiagnostic(
                name="TelemetryDistributedTracing",
                status="HEALTHY" if len(recent_spans) > 0 else "DEGRADED",
                latency_ms=round(trace_latency, 2),
                details={"recent_spans_count": len(recent_spans)},
            )
        )

        # Compute overall status
        is_all_healthy = all(s.status == "HEALTHY" for s in subsystems)
        overall = "HEALTHY" if is_all_healthy else "DEGRADED"

        logger.info(
            f"[ObservabilityDiagnostics] Health check completed in {(time.time() - start_ts)*1000:.1f}ms: "
            f"Overall={overall}, VRAM_Compliant={vram_compliant}"
        )

        return ObservabilityHealthReport(
            generated_at=time.time(),
            overall_status=overall,
            vram_budget_compliant=vram_compliant,
            diagnostics=subsystems,
        )


observability_diagnostics = ObservabilityDiagnosticsEngine()
