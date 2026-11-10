"""Cognitive Root Cause Analysis (RCA) and Causal Graph Inference Engine.

Implements Stage 9 Unified Observability Architecture:
- Models dependencies between system components as a directed causal graph.
- Correlates symptom alerts with upstream failure dependencies.
- Computes Bayesian root-cause likelihood scores and generates actionable remediation guidance.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CausalNode:
    node_id: str
    component_name: str
    failure_probability_prior: float
    upstream_dependencies: list[str] = field(default_factory=list)


@dataclass
class SymptomAlert:
    alert_id: str
    component_name: str
    severity: str
    metric_name: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class RootCauseHypothesis:
    root_component: str
    causal_path: list[str]
    posterior_probability: float
    remediation_suggestion: str


class CognitiveRootCauseAnalyzer:
    """Infers the primary root cause behind multi-service cascading failures."""

    def __init__(self) -> None:
        self._topology: dict[str, CausalNode] = {}
        self._symptom_history: list[SymptomAlert] = []
        self._register_default_topology()

    def _register_default_topology(self) -> None:
        # Standard COPPER dependency chain: Storage/GPU -> InferenceEngine -> ModelRouter -> Agent -> API
        self.register_node("gpu_vram", "Hardware VRAM Subsystem", prior=0.08)
        self.register_node("disk_io", "SQLite WAL Storage", prior=0.05)
        self.register_node("inference_engine", "Local Model Inference", prior=0.10, upstreams=["gpu_vram"])
        self.register_node("queue_manager", "Inference Queue Manager", prior=0.06, upstreams=["inference_engine"])
        self.register_node("agent_runtime", "Agent Orchestration Engine", prior=0.07, upstreams=["queue_manager", "disk_io"])
        self.register_node("api_gateway", "FastAPI Gateway", prior=0.04, upstreams=["agent_runtime"])

    def register_node(
        self,
        node_id: str,
        component_name: str,
        prior: float = 0.05,
        upstreams: Optional[list[str]] = None,
    ) -> None:
        self._topology[node_id] = CausalNode(
            node_id=node_id,
            component_name=component_name,
            failure_probability_prior=prior,
            upstream_dependencies=upstreams or [],
        )

    def record_symptom(self, alert: SymptomAlert) -> None:
        self._symptom_history.append(alert)

    def analyze_root_cause(self, active_symptoms: list[SymptomAlert]) -> list[RootCauseHypothesis]:
        """Traverse causal dependencies backwards from affected nodes to compute posterior root-cause probabilities."""
        if not active_symptoms:
            return []

        affected_nodes = {s.component_name for s in active_symptoms}
        candidates: dict[str, list[str]] = {}  # candidate -> path to symptom

        for symptom_node in affected_nodes:
            # Trace upstreams
            queue = [[symptom_node]]
            while queue:
                path = queue.pop(0)
                curr = path[-1]
                node_obj = self._topology.get(curr)
                if not node_obj or not node_obj.upstream_dependencies:
                    # Root reached
                    if curr not in candidates:
                        candidates[curr] = path
                else:
                    for up in node_obj.upstream_dependencies:
                        queue.append(path + [up])

        # Compute posterior scores
        hypotheses: list[RootCauseHypothesis] = []
        for root_id, path in candidates.items():
            node = self._topology.get(root_id)
            prior = node.failure_probability_prior if node else 0.1
            # Severity multiplier
            weight = 1.0 + (0.5 if root_id in affected_nodes else 0.2)
            score = min(0.99, prior * weight * len(path))

            # Suggestion based on root component
            if "gpu" in root_id:
                remediation = "Trigger dynamic model unloading or downgrade quantization tier to INT4."
            elif "disk" in root_id:
                remediation = "Run WAL checkpointing and storage quota reclamation."
            elif "inference" in root_id:
                remediation = "Reset model runtime session and flush pending queue batch."
            else:
                remediation = f"Restart service {root_id} and inspect active thread pool."

            hypotheses.append(
                RootCauseHypothesis(
                    root_component=root_id,
                    causal_path=list(reversed(path)),
                    posterior_probability=round(score, 2),
                    remediation_suggestion=remediation,
                )
            )

        hypotheses.sort(key=lambda h: h.posterior_probability, reverse=True)
        return hypotheses
