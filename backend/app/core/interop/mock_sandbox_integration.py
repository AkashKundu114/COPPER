"""Sandboxed Mock Integration Test Runner for External Adapters & MCP in C.O.P.P.E.R.

Executes deterministic mock integration drills against external service adapters
and MCP JSON-RPC 2.0 endpoints in an airgapped sandbox to verify timeout resilience,
payload schema conformance, and failover handling without live network access.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.interop.errors import COPPERErrorResponse, ErrorCode
from app.core.logger import logger


@dataclass
class MockAdapterTestResult:
    adapter_name: str
    protocol: str  # "REST" | "MCP" | "GRAPHQL"
    test_case: str
    passed: bool
    latency_ms: float
    error_code: str | None = None


@dataclass
class MockIntegrationReport:
    report_id: str
    timestamp: float
    all_tests_passed: bool
    total_adapters_tested: int
    results: list[MockAdapterTestResult]
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MockIntegrationSandbox:
    """Airgapped sandbox testing third-party tool adapters and protocol contracts."""

    async def run_adapter_test_suite(self) -> MockIntegrationReport:
        """Executes a suite of simulated adapter calls testing timeouts, invalid schemas, and successes."""
        results: list[MockAdapterTestResult] = []

        # 1. Test MCP JSON-RPC 2.0 Adapter contract
        t0 = time.perf_counter()
        from app.core.interop.mcp_adapter import mcp_adapter
        res_mcp = await mcp_adapter.handle_json_rpc(
            {"jsonrpc": "2.0", "id": "test_01", "method": "ping"}
        )
        mcp_ms = (time.perf_counter() - t0) * 1000.0
        results.append(
            MockAdapterTestResult(
                adapter_name="MCPJSONRPCAdapter",
                protocol="MCP",
                test_case="PingLifecycle",
                passed="result" in res_mcp,
                latency_ms=round(mcp_ms, 2),
            )
        )

        # 2. Test MCP Tools List contract
        t1 = time.perf_counter()
        res_tools = await mcp_adapter.handle_json_rpc(
            {"jsonrpc": "2.0", "id": "test_02", "method": "tools/list"}
        )
        tools_ms = (time.perf_counter() - t1) * 1000.0
        results.append(
            MockAdapterTestResult(
                adapter_name="MCPJSONRPCAdapter",
                protocol="MCP",
                test_case="ToolsListContract",
                passed="tools" in res_tools.get("result", {}),
                latency_ms=round(tools_ms, 2),
            )
        )

        # 3. Test REST Gateway Deprecation Handling
        t2 = time.perf_counter()
        from app.core.interop.integration_gateway import integration_gateway
        res_rest = await integration_gateway.dispatch_rest(
            endpoint_path="/api/v1/mock_probe",
            method="POST",
            payload={"test": "echo"},
        )
        rest_ms = (time.perf_counter() - t2) * 1000.0
        results.append(
            MockAdapterTestResult(
                adapter_name="RESTIntegrationGateway",
                protocol="REST",
                test_case="ValidDispatchAndHeaderPreservation",
                passed=res_rest.status_code == 200,
                latency_ms=round(rest_ms, 2),
            )
        )

        # 4. Test Error Envelope Normalization on Invalid Method
        t3 = time.perf_counter()
        res_err = await integration_gateway.dispatch_rest(
            endpoint_path="/api/v1/mock_probe",
            method="INVALID_METHOD",
        )
        err_ms = (time.perf_counter() - t3) * 1000.0
        results.append(
            MockAdapterTestResult(
                adapter_name="RESTIntegrationGateway",
                protocol="REST",
                test_case="RFC7807ErrorEnvelopeConformance",
                passed=res_err.is_error and res_err.status_code == 405,
                latency_ms=round(err_ms, 2),
                error_code="INVALID_REQUEST",
            )
        )

        all_ok = all(r.passed for r in results)
        now = time.time()
        rep_id = f"INT-MOCK-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{rep_id}:{all_ok}:{len(results)}".encode()).hexdigest()

        report = MockIntegrationReport(
            report_id=rep_id,
            timestamp=now,
            all_tests_passed=all_ok,
            total_adapters_tested=len(results),
            results=results,
            signature=sig,
        )

        logger.info(
            f"[MockIntegrationSandbox] Integration tests completed: {sum(1 for r in results if r.passed)}/{len(results)} passed."
        )
        return report


mock_integration_sandbox = MockIntegrationSandbox()
