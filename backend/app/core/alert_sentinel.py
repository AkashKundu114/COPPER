"""In-App Alert Sentinel and Anomaly Detection Engine.

Provides local-first alerting and health monitoring independent of external Prometheus Alertmanager,
enforcing VRAM, CPU, queue, agent, and security operational guarantees.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.core.logger import logger
from app.core.metrics import metrics_registry


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    id: str
    name: str
    severity: AlertSeverity
    message: str
    component: str
    current_value: float | str
    threshold: float | str
    remediation: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["formatted_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        return data


class AlertSentinel:
    """Evaluates local operational health metrics against safety thresholds."""

    def __init__(self):
        self.vram_threshold_ratio: float = 0.90
        self.cpu_threshold_ratio: float = 0.90
        self.ram_threshold_ratio: float = 0.90
        self.queue_depth_threshold: int = 5
        self.agent_failure_rate_threshold: float = 0.20
        self.security_event_spike_threshold: int = 5

        # Tracking state
        self._recent_agent_runs: list[bool] = []
        self._model_loading_failures: int = 0
        self._security_incident_count: int = 0
        self._telemetry_drop_count: int = 0

    def reset(self) -> None:
        """Resets tracking counters for testing and clean slate."""
        self._recent_agent_runs.clear()
        self._model_loading_failures = 0
        self._security_incident_count = 0
        self._telemetry_drop_count = 0

    def record_agent_execution(self, success: bool) -> None:
        self._recent_agent_runs.append(success)
        if len(self._recent_agent_runs) > 50:
            self._recent_agent_runs.pop(0)

    def record_model_load_failure(self) -> None:
        self._model_loading_failures += 1

    def record_security_incident(self) -> None:
        self._security_incident_count += 1

    def record_telemetry_failure(self) -> None:
        self._telemetry_drop_count += 1

    def evaluate_active_alerts(self, sample_hardware: bool = True) -> list[Alert]:
        """Scans all system metrics and returns list of actively firing alerts."""
        if sample_hardware:
            metrics_registry.sample_system_hardware()
        alerts: list[Alert] = []

        # 1. GPU VRAM Pressure
        vram_used = metrics_registry.vram_used_bytes.get_samples()[0].value
        vram_total = metrics_registry.vram_total_bytes.get_samples()[0].value
        if vram_total > 0:
            ratio = vram_used / vram_total
            headroom_mb = (vram_total - vram_used) / (1024 * 1024)
            if ratio >= self.vram_threshold_ratio:
                alerts.append(
                    Alert(
                        id="gpu_vram_pressure",
                        name="GPUVRAMPressure",
                        severity=AlertSeverity.CRITICAL if ratio >= 0.95 else AlertSeverity.WARNING,
                        message=f"VRAM utilization at {ratio*100:.1f}% ({headroom_mb:.0f}MB headroom remaining on 8GB budget).",
                        component="gpu_activation",
                        current_value=round(ratio, 3),
                        threshold=self.vram_threshold_ratio,
                        remediation="Trigger model hot-swap unload of heavy models or reduce image generation dimensions.",
                    )
                )

        # 2. Host CPU Exhaustion
        cpu_ratio = metrics_registry.cpu_utilization.get_samples()[0].value
        if cpu_ratio >= self.cpu_threshold_ratio:
            alerts.append(
                Alert(
                    id="cpu_exhaustion",
                    name="HostCPUExhaustion",
                    severity=AlertSeverity.WARNING,
                    message=f"Host CPU usage sustained at {cpu_ratio*100:.1f}%.",
                    component="host_system",
                    current_value=round(cpu_ratio, 3),
                    threshold=self.cpu_threshold_ratio,
                    remediation="Check for long-running sandboxed subprocesses or intensive vector indexing tasks.",
                )
            )

        # 3. Host RAM Exhaustion
        ram_ratio = metrics_registry.ram_utilization.get_samples()[0].value
        if ram_ratio >= self.ram_threshold_ratio:
            alerts.append(
                Alert(
                    id="ram_exhaustion",
                    name="HostRAMExhaustion",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Host system RAM usage at {ram_ratio*100:.1f}%.",
                    component="host_system",
                    current_value=round(ram_ratio, 3),
                    threshold=self.ram_threshold_ratio,
                    remediation="Clear in-memory cache and unload dormant Python worker threads.",
                )
            )

        # 4. Inference Queue Saturation
        queue_depth = metrics_registry.inference_queue_depth.get_samples()[0].value
        if queue_depth >= self.queue_depth_threshold:
            alerts.append(
                Alert(
                    id="inference_queue_saturation",
                    name="InferenceQueueSaturation",
                    severity=AlertSeverity.WARNING,
                    message=f"Inference queue backlog has reached {int(queue_depth)} requests.",
                    component="inference_queue",
                    current_value=int(queue_depth),
                    threshold=self.queue_depth_threshold,
                    remediation="Throttle client request rate or reduce concurrent agent generation loops.",
                )
            )

        # 5. Repeated Agent Failures
        if len(self._recent_agent_runs) >= 10:
            failures = sum(1 for s in self._recent_agent_runs if not s)
            fail_rate = failures / len(self._recent_agent_runs)
            if fail_rate >= self.agent_failure_rate_threshold:
                alerts.append(
                    Alert(
                        id="agent_failure_rate_high",
                        name="HighAgentFailureRate",
                        severity=AlertSeverity.CRITICAL,
                        message=f"Agent failure rate at {fail_rate*100:.1f}% across last {len(self._recent_agent_runs)} turns.",
                        component="agent_orchestration",
                        current_value=round(fail_rate, 2),
                        threshold=self.agent_failure_rate_threshold,
                        remediation="Inspect Ollama daemon connection, target prompt formats, and tool permissions.",
                    )
                )

        # 6. Model Loading Failures
        if self._model_loading_failures > 0:
            alerts.append(
                Alert(
                    id="model_loading_failures",
                    name="ModelLoadFailures",
                    severity=AlertSeverity.CRITICAL,
                    message=f"{self._model_loading_failures} model hot-swap loading operations failed.",
                    component="model_tier_manager",
                    current_value=self._model_loading_failures,
                    threshold=0,
                    remediation="Verify Ollama model tags and disk storage in ai-models directory.",
                )
            )

        # 7. Database Connectivity Failure
        db_health = metrics_registry.database_status.get_samples()[0].value
        if db_health < 1.0:
            alerts.append(
                Alert(
                    id="database_connectivity_failure",
                    name="DatabaseConnectivityDown",
                    severity=AlertSeverity.CRITICAL,
                    message="Database connection probe failed; vector store or relational database is degraded.",
                    component="database",
                    current_value=db_health,
                    threshold=1.0,
                    remediation="Inspect database file permissions or check ChromaDB / SQLite / Postgres processes.",
                )
            )

        # 8. Security Incidents Spike
        if self._security_incident_count >= self.security_event_spike_threshold:
            alerts.append(
                Alert(
                    id="security_incident_spike",
                    name="SecurityIncidentSpike",
                    severity=AlertSeverity.CRITICAL,
                    message=f"{self._security_incident_count} security interventions (Guardian/Firewall/Auth) recorded.",
                    component="guardian_security",
                    current_value=self._security_incident_count,
                    threshold=self.security_event_spike_threshold,
                    remediation="Review security audit trail at /api/v1/audit/ for potential prompt injection or unauthorized access.",
                )
            )

        # 9. Telemetry Pipeline Failure
        pipeline_status = metrics_registry.telemetry_pipeline_status.get_samples()[0].value
        if pipeline_status < 1.0 or self._telemetry_drop_count > 0:
            alerts.append(
                Alert(
                    id="telemetry_pipeline_degraded",
                    name="TelemetryPipelineDegraded",
                    severity=AlertSeverity.WARNING,
                    message=f"Telemetry pipeline degraded: {self._telemetry_drop_count} spans dropped or exporter offline.",
                    component="telemetry_otel",
                    current_value=self._telemetry_drop_count,
                    threshold=0,
                    remediation="Check Tempo OTLP endpoint and network connectivity; local buffered tracing remains active.",
                )
            )

        return alerts


alert_sentinel = AlertSentinel()
