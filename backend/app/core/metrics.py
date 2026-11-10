"""Native Prometheus Metrics Registry and System Hardware Telemetry Engine.

Provides zero-dependency in-memory Prometheus metric collection and exposition,
supporting gauges, counters, histograms, and hardware sampling under the 8GB VRAM constraint.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.core.logger import logger


@dataclass
class MetricSample:
    name: str
    labels: dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: float = field(default_factory=time.time)


class Counter:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)

    def inc(self, amount: float | dict[str, str] = 1.0, labels: dict[str, str] | None = None) -> None:
        if isinstance(amount, dict):
            labels, amount = amount, 1.0
        key = tuple(sorted((labels or {}).items()))
        self._values[key] += max(0.0, float(amount))

    def get(self, labels: dict[str, str] | None = None) -> float:
        key = tuple(sorted((labels or {}).items()))
        return self._values.get(key, 0.0)

    def get_samples(self) -> list[MetricSample]:
        samples = []
        for key, val in self._values.items():
            samples.append(MetricSample(name=self.name, labels=dict(key), value=val))
        if not samples:
            samples.append(MetricSample(name=self.name, labels={}, value=0.0))
        return samples


class Gauge:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        key = tuple(sorted((labels or {}).items()))
        self._values[key] = float(value)

    def inc(self, amount: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = tuple(sorted((labels or {}).items()))
        self._values[key] += float(amount)

    def dec(self, amount: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = tuple(sorted((labels or {}).items()))
        self._values[key] -= float(amount)

    def get(self, labels: dict[str, str] | None = None) -> float:
        key = tuple(sorted((labels or {}).items()))
        return self._values.get(key, 0.0)

    def get_samples(self) -> list[MetricSample]:
        samples = []
        for key, val in self._values.items():
            samples.append(MetricSample(name=self.name, labels=dict(key), value=val))
        if not samples:
            samples.append(MetricSample(name=self.name, labels={}, value=0.0))
        return samples


class Histogram:
    def __init__(self, name: str, description: str, buckets: list[float] | None = None):
        self.name = name
        self.description = description
        self.buckets = sorted(buckets or [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        self._counts: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._sums: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._bucket_counts: dict[tuple[tuple[str, str], ...], dict[float, int]] = defaultdict(
            lambda: {b: 0 for b in self.buckets}
        )

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        val = max(0.0, float(value))
        key = tuple(sorted((labels or {}).items()))
        self._counts[key] += 1.0
        self._sums[key] += val
        bucket_dict = self._bucket_counts[key]
        for b in self.buckets:
            if val <= b:
                bucket_dict[b] += 1

    def get(self, labels: dict[str, str] | None = None) -> dict[str, Any]:
        key = tuple(sorted((labels or {}).items()))
        return {
            "count": self._counts.get(key, 0.0),
            "sum": self._sums.get(key, 0.0),
            "buckets": dict(self._bucket_counts.get(key, {b: 0 for b in self.buckets})),
        }

    def get_samples(self) -> list[MetricSample]:
        samples = []
        for key, count in self._counts.items():
            base_labels = dict(key)
            bucket_dict = self._bucket_counts[key]
            for b in self.buckets:
                b_labels = {**base_labels, "le": str(b)}
                samples.append(MetricSample(name=f"{self.name}_bucket", labels=b_labels, value=float(bucket_dict[b])))
            inf_labels = {**base_labels, "le": "+Inf"}
            samples.append(MetricSample(name=f"{self.name}_bucket", labels=inf_labels, value=count))
            samples.append(MetricSample(name=f"{self.name}_sum", labels=base_labels, value=self._sums[key]))
            samples.append(MetricSample(name=f"{self.name}_count", labels=base_labels, value=count))
        return samples


class PrometheusMetricsRegistry:
    """Central metrics registry exposing Prometheus exposition format."""

    def __init__(self):
        # 1. Hardware utilization
        self.cpu_utilization = Gauge("copper_cpu_utilization_ratio", "CPU utilization ratio (0.0 - 1.0)")
        self.ram_utilization = Gauge("copper_ram_utilization_ratio", "RAM utilization ratio (0.0 - 1.0)")
        self.ram_used_bytes = Gauge("copper_ram_used_bytes", "RAM used in bytes")
        self.ram_total_bytes = Gauge("copper_ram_total_bytes", "RAM total in bytes")
        self.gpu_utilization = Gauge("copper_gpu_utilization_ratio", "GPU compute utilization ratio (0.0 - 1.0)")
        self.vram_used_bytes = Gauge("copper_vram_used_bytes", "GPU VRAM used in bytes")
        self.vram_total_bytes = Gauge("copper_vram_total_bytes", "GPU VRAM total in bytes (8GB budget)")

        # 2. Models & Inference
        self.model_loading_seconds = Histogram(
            "copper_model_loading_seconds",
            "Duration in seconds to hot-swap / load a model into VRAM",
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )
        self.llm_inference_duration_seconds = Histogram(
            "copper_llm_inference_duration_seconds",
            "End-to-end LLM inference latency in seconds",
            buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
        )
        self.llm_tokens_generated = Counter("copper_llm_tokens_generated_total", "Total tokens generated across all models")
        self.llm_prompt_tokens = Counter("copper_llm_prompt_tokens_total", "Total prompt tokens evaluated")
        self.llm_tokens_per_second = Gauge("copper_llm_tokens_per_second", "Instantaneous token generation velocity (tokens/sec)")
        self.inference_queue_depth = Gauge("copper_inference_queue_depth", "Current queue depth of pending inference tasks")

        # 3. Agents & Tools
        self.agent_executions = Counter("copper_agent_executions_total", "Total agent task executions")
        self.agent_handoffs = Counter("copper_agent_handoffs_total", "Total inter-agent delegation handoffs")
        self.tool_executions = Counter("copper_tool_executions_total", "Total tool executions")
        self.tool_execution_duration_seconds = Histogram(
            "copper_tool_execution_duration_seconds",
            "Tool execution duration in seconds",
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 3.0, 10.0, 30.0],
        )

        # 4. HTTP & Traffic
        self.http_requests = Counter("copper_http_requests_total", "Total HTTP requests served")
        self.http_request_duration_seconds = Histogram(
            "copper_http_request_duration_seconds",
            "HTTP request duration in seconds",
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        )

        # 5. Memory & Database
        self.memory_retrieval_duration_seconds = Histogram(
            "copper_memory_retrieval_duration_seconds",
            "Epistemic memory retrieval latency in seconds",
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 1.0],
        )
        self.database_status = Gauge("copper_database_connection_status", "Database connection health (1 = healthy, 0 = degraded)")

        # 6. Security & Guardian
        self.security_events = Counter("copper_security_events_total", "Security events intercepted by firewall and auth")
        self.guardian_verdicts = Counter("copper_guardian_verdicts_total", "Guardian safety verdicts evaluated")
        self.telemetry_pipeline_status = Gauge("copper_telemetry_pipeline_status", "Telemetry exporter status (1 = healthy, 0 = degraded)")

        self._all_metrics = [
            self.cpu_utilization,
            self.ram_utilization,
            self.ram_used_bytes,
            self.ram_total_bytes,
            self.gpu_utilization,
            self.vram_used_bytes,
            self.vram_total_bytes,
            self.model_loading_seconds,
            self.llm_inference_duration_seconds,
            self.llm_tokens_generated,
            self.llm_prompt_tokens,
            self.llm_tokens_per_second,
            self.inference_queue_depth,
            self.agent_executions,
            self.agent_handoffs,
            self.tool_executions,
            self.tool_execution_duration_seconds,
            self.http_requests,
            self.http_request_duration_seconds,
            self.memory_retrieval_duration_seconds,
            self.database_status,
            self.security_events,
            self.guardian_verdicts,
            self.telemetry_pipeline_status,
        ]
        self._manual_hardware_set = False

    def sample_system_hardware(self, force: bool = False) -> None:
        """Samples host CPU, RAM, and GPU utilization and updates Prometheus gauges."""
        if self._manual_hardware_set and not force:
            return

        try:
            from app.api.routes.system import _get_cpu_usage_and_info, _get_ram_info
            from app.core.gpu_activation import get_gpu_telemetry

            _, _, cpu_pct = _get_cpu_usage_and_info()
            self.cpu_utilization.set(round(cpu_pct / 100.0, 4))

            ram_total_gb, ram_used_gb, ram_pct = _get_ram_info()
            self.ram_utilization.set(round(ram_pct / 100.0, 4))
            self.ram_used_bytes.set(ram_used_gb * (1024**3))
            self.ram_total_bytes.set(ram_total_gb * (1024**3))

            gpu_data = get_gpu_telemetry()
            vram_used = float(gpu_data.get("vram_used_mb", 0.0)) * 1024 * 1024
            vram_total = float(gpu_data.get("vram_total_mb", 8192.0)) * 1024 * 1024
            gpu_util = float(gpu_data.get("gpu_util_pct", 0.0)) / 100.0

            self.gpu_utilization.set(round(gpu_util, 4))
            self.vram_used_bytes.set(vram_used)
            self.vram_total_bytes.set(vram_total)
            self.database_status.set(1.0)
            self.telemetry_pipeline_status.set(1.0)
        except Exception as e:
            logger.debug(f"[Metrics] Hardware sample warning: {e}")

    def record_hardware_metrics(
        self,
        cpu_ratio: float | None = None,
        ram_used: float | None = None,
        ram_total: float | None = None,
        gpu_ratio: float | None = None,
        vram_used: float | None = None,
        vram_total: float | None = None,
    ) -> None:
        self._manual_hardware_set = True
        if cpu_ratio is not None:
            self.cpu_utilization.set(float(cpu_ratio))
        if ram_used is not None:
            self.ram_used_bytes.set(float(ram_used))
        if ram_total is not None:
            self.ram_total_bytes.set(float(ram_total))
        if ram_used is not None and ram_total is not None and ram_total > 0:
            self.ram_utilization.set(round(ram_used / ram_total, 4))
        if gpu_ratio is not None:
            self.gpu_utilization.set(float(gpu_ratio))
        if vram_used is not None:
            self.vram_used_bytes.set(float(vram_used))
        if vram_total is not None:
            self.vram_total_bytes.set(float(vram_total))

    def record_agent_execution(self, agent_type: str, status: str = "success", duration_s: float = 0.0) -> None:
        self.agent_executions.inc(1.0, {"agent_type": agent_type, "status": status})

    def record_llm_inference(
        self,
        model_name: str,
        duration_s: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        tps: float | None = None,
    ) -> None:
        self.llm_inference_duration_seconds.observe(duration_s, {"model_name": model_name})
        if prompt_tokens > 0:
            self.llm_prompt_tokens.inc(float(prompt_tokens), {"model_name": model_name})
        if completion_tokens > 0:
            self.llm_tokens_generated.inc(float(completion_tokens), {"model_name": model_name})
        if tps is not None:
            self.llm_tokens_per_second.set(float(tps), {"model_name": model_name})
        elif duration_s > 0 and completion_tokens > 0:
            self.llm_tokens_per_second.set(round(completion_tokens / duration_s, 2), {"model_name": model_name})

    def record_tool_execution(self, tool_name: str, duration_s: float) -> None:
        self.tool_executions.inc(1.0, {"tool_name": tool_name})
        self.tool_execution_duration_seconds.observe(duration_s, {"tool_name": tool_name})

    def record_security_event(self, event_type: str) -> None:
        self.security_events.inc(1.0, {"event_type": event_type})

    def record_guardian_verdict(self, verdict: str) -> None:
        self.guardian_verdicts.inc(1.0, {"verdict": verdict.lower()})

    def update_queue_depth(self, depth: int) -> None:
        self.inference_queue_depth.set(float(depth))

    def record_database_health(self, is_healthy: bool) -> None:
        self.database_status.set(1.0 if is_healthy else 0.0)

    def record_telemetry_health(self, is_healthy: bool) -> None:
        self.telemetry_pipeline_status.set(1.0 if is_healthy else 0.0)

    def record_http_request(self, method: str, path: str, status_code: int, duration_s: float) -> None:
        self.http_requests.inc(1.0, {"method": method, "path": path, "status": str(status_code)})
        self.http_request_duration_seconds.observe(duration_s, {"method": method, "path": path})

    def render_prometheus_exposition(self) -> str:
        """Renders standard Prometheus exposition format string."""
        self.sample_system_hardware()
        lines: list[str] = []

        for m in self._all_metrics:
            lines.append(f"# HELP {m.name} {m.description}")
            m_type = (
                "counter"
                if isinstance(m, Counter)
                else "histogram"
                if isinstance(m, Histogram)
                else "gauge"
            )
            lines.append(f"# TYPE {m.name} {m_type}")

            for sample in m.get_samples():
                if sample.labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(sample.labels.items()))
                    lines.append(f"{sample.name}{{{label_str}}} {sample.value}")
                else:
                    lines.append(f"{sample.name} {sample.value}")

        return "\n".join(lines) + "\n"

    def get_metrics_summary(self) -> dict[str, Any]:
        """Returns JSON metrics summary for local dashboards."""
        self.sample_system_hardware()
        return {
            "hardware": {
                "cpu_utilization_ratio": self.cpu_utilization.get_samples()[0].value,
                "ram_utilization_ratio": self.ram_utilization.get_samples()[0].value,
                "gpu_utilization_ratio": self.gpu_utilization.get_samples()[0].value,
                "vram_used_bytes": self.vram_used_bytes.get_samples()[0].value,
                "vram_total_bytes": self.vram_total_bytes.get_samples()[0].value,
            },
            "inference": {
                "tokens_generated": sum(s.value for s in self.llm_tokens_generated.get_samples()),
                "prompt_tokens": sum(s.value for s in self.llm_prompt_tokens.get_samples()),
                "tokens_per_second": self.llm_tokens_per_second.get_samples()[0].value,
                "queue_depth": self.inference_queue_depth.get_samples()[0].value,
            },
            "agents": {
                "total_executions": sum(s.value for s in self.agent_executions.get_samples()),
                "total_handoffs": sum(s.value for s in self.agent_handoffs.get_samples()),
                "total_tool_executions": sum(s.value for s in self.tool_executions.get_samples()),
            },
            "security": {
                "total_violations": sum(s.value for s in self.security_events.get_samples()),
                "total_guardian_verdicts": sum(s.value for s in self.guardian_verdicts.get_samples()),
            },
            "database": {
                "status": "healthy" if self.database_status.get_samples()[0].value == 1.0 else "degraded",
            },
            "status": "online",
        }


metrics_registry = PrometheusMetricsRegistry()
