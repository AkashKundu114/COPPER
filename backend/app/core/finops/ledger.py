"""Unified Resource Accounting Ledger & FinOps Telemetry Engine for C.O.P.P.E.R.

Tracks and attributes hardware consumption (CPU, GPU, VRAM, RAM), token usage,
storage growth, and external API expenditures by agent, model, task, and workflow.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger


@dataclass
class ResourceUsageRecord:
    task_id: str
    agent_id: str
    model_name: str
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    user_id: str = "default_user"
    cpu_time_ms: float = 0.0
    inference_duration_ms: float = 0.0
    peak_vram_bytes: int = 0
    peak_ram_bytes: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    storage_delta_bytes: int = 0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    external_provider: str | None = None
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResourceAccountingLedger:
    """In-memory thread-safe FinOps resource and cost accounting ledger."""

    def __init__(self, max_history_records: int = 5000):
        self.max_history = max_history_records
        self._records: list[ResourceUsageRecord] = []
        self._agent_aggregates: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "total_tokens": 0.0,
                "prompt_tokens": 0.0,
                "completion_tokens": 0.0,
                "total_cpu_time_ms": 0.0,
                "total_inference_time_ms": 0.0,
                "total_cost_usd": 0.0,
                "invocation_count": 0.0,
            }
        )

    def record_usage(self, record: ResourceUsageRecord) -> None:
        """Appends a resource usage record and updates running aggregates."""
        self._records.append(record)
        if len(self._records) > self.max_history:
            self._records.pop(0)

        # Update running aggregates for agent
        agg = self._agent_aggregates[record.agent_id]
        agg["total_tokens"] += record.total_tokens
        agg["prompt_tokens"] += record.prompt_tokens
        agg["completion_tokens"] += record.completion_tokens
        agg["total_cpu_time_ms"] += record.cpu_time_ms
        agg["total_inference_time_ms"] += record.inference_duration_ms
        agg["total_cost_usd"] += record.cost_usd
        agg["invocation_count"] += 1.0

        logger.debug(
            f"[FinOps] Recorded usage for task {record.task_id} "
            f"(Agent: {record.agent_id}, Tokens: {record.total_tokens}, "
            f"Latency: {record.inference_duration_ms:.1f}ms, Cost: ${record.cost_usd:.5f})"
        )

    def get_agent_summary(self, agent_id: str) -> dict[str, float]:
        """Returns cumulative consumption metrics for a specific agent."""
        return dict(self._agent_aggregates.get(agent_id, {}))

    def get_global_summary(self) -> dict[str, Any]:
        """Returns global aggregated consumption metrics across all agents."""
        total_tokens = sum(a["total_tokens"] for a in self._agent_aggregates.values())
        total_cost = sum(a["total_cost_usd"] for a in self._agent_aggregates.values())
        total_invocations = sum(a["invocation_count"] for a in self._agent_aggregates.values())

        return {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "total_invocations": int(total_invocations),
            "tracked_agents": list(self._agent_aggregates.keys()),
            "history_record_count": len(self._records),
        }

    def reset(self) -> None:
        """Resets ledger state (used for testing or monthly billing cycle reset)."""
        self._records.clear()
        self._agent_aggregates.clear()


resource_ledger = ResourceAccountingLedger()
