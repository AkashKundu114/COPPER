"""Synthetic User Journey Probes & SLO Verification Watchdog for C.O.P.P.E.R.

Simulates end-to-end user interactions (prompt input -> security check -> tool contract ->
memory mutation -> audit notarization) to verify operational Service Level Objectives (SLOs)
and measure continuous pipeline latency.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.metrics import metrics_registry
from app.core.telemetry_coordinator import telemetry_coordinator


@dataclass
class SyntheticStepResult:
    step_name: str
    duration_ms: float
    passed: bool
    details: str = ""


@dataclass
class SyntheticProbeReport:
    probe_id: str
    timestamp: float
    all_steps_passed: bool
    total_pipeline_latency_ms: float
    slo_target_ms: float
    slo_compliant: bool
    steps: list[SyntheticStepResult]
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SyntheticProbeWatchdog:
    """Executes scheduled synthetic user journeys to validate real-time operational SLOs."""

    DEFAULT_SLO_TARGET_MS: float = 500.0  # End-to-end local latency budget

    def __init__(self, slo_target_ms: float = DEFAULT_SLO_TARGET_MS):
        self.slo_target_ms = slo_target_ms
        self.metrics = metrics_registry
        self.telemetry = telemetry_coordinator

    async def execute_synthetic_journey(self) -> SyntheticProbeReport:
        """Executes a complete 4-step synthetic transaction across core subsystems."""
        t_start = time.perf_counter()
        steps: list[SyntheticStepResult] = []

        # Step 1: Security Preflight & PII Firewall Sanitization
        t0 = time.perf_counter()
        from app.core.data_firewall import classify_and_redact
        res_fw = classify_and_redact("Synthetic test payload with safe queries.")
        fw_ms = (time.perf_counter() - t0) * 1000.0
        steps.append(
            SyntheticStepResult(
                step_name="SecurityPreflight",
                duration_ms=round(fw_ms, 2),
                passed=res_fw.classification is not None,
                details=f"Classification={res_fw.classification.value}",
            )
        )

        # Step 2: Context Optimization & Token Estimation
        t1 = time.perf_counter()
        from app.ai.memory.context_optimizer import context_optimizer
        res_opt = context_optimizer.optimize_context(["Context memory test snippet"], token_budget=128)
        opt_ms = (time.perf_counter() - t1) * 1000.0
        steps.append(
            SyntheticStepResult(
                step_name="ContextOptimization",
                duration_ms=round(opt_ms, 2),
                passed=res_opt.optimized_estimated_tokens > 0,
                details=f"Tokens={res_opt.optimized_estimated_tokens}",
            )
        )

        # Step 3: Tool Execution Contract Simulation
        t2 = time.perf_counter()
        from app.ai.tools.registry import BaseTool
        from app.core.interop.tool_contract import tool_contract_wrapper

        async def dummy_fn(param: str):
            return f"Processed: {param}"

        dummy_tool = BaseTool(
            name="synthetic_probe_tool",
            description="Synthetic probe test tool",
            parameters={"type": "object", "properties": {"param": {"type": "string"}}, "required": ["param"]},
            func=dummy_fn,
        )
        tool_res = await tool_contract_wrapper.execute_contract(dummy_tool, {"param": "ok"})
        tool_ms = (time.perf_counter() - t2) * 1000.0
        steps.append(
            SyntheticStepResult(
                step_name="ToolContractExecution",
                duration_ms=round(tool_ms, 2),
                passed=tool_res.success,
                details="Tool contract executed cleanly",
            )
        )

        # Step 4: Audit Event Sealing
        t3 = time.perf_counter()
        from app.core.audit.audit_event import AuditCategory, AuditEvent, AuditOutcome
        ev = AuditEvent(
            sequence_num=999,
            category=AuditCategory.TOOL_EXECUTED,
            actor="synthetic_probe_watchdog",
            action="execute_probe_journey",
            target_resource="copper_pipeline",
            outcome=AuditOutcome.SUCCESS,
            prev_hash="0" * 64,
        )
        ev.seal()
        audit_ms = (time.perf_counter() - t3) * 1000.0
        steps.append(
            SyntheticStepResult(
                step_name="AuditNotarization",
                duration_ms=round(audit_ms, 2),
                passed=len(ev.entry_hash) == 64,
                details=f"Hash={ev.entry_hash[:12]}...",
            )
        )

        total_latency = (time.perf_counter() - t_start) * 1000.0
        all_passed = all(s.passed for s in steps)
        slo_ok = total_latency <= self.slo_target_ms

        now = time.time()
        probe_id = f"SYNTH-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{probe_id}:{total_latency}:{all_passed}".encode()).hexdigest()

        report = SyntheticProbeReport(
            probe_id=probe_id,
            timestamp=now,
            all_steps_passed=all_passed,
            total_pipeline_latency_ms=round(total_latency, 2),
            slo_target_ms=self.slo_target_ms,
            slo_compliant=slo_ok,
            steps=steps,
            signature=sig,
        )

        logger.info(
            f"[SyntheticProbeWatchdog] Synthetic journey completed in {total_latency:.2f}ms "
            f"(Passed: {all_passed}, SLO compliant: {slo_ok})"
        )
        return report


synthetic_probe_watchdog = SyntheticProbeWatchdog()
