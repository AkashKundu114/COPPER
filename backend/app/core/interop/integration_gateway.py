"""Unified Multi-Protocol Integration Gateway for C.O.P.P.E.R.

Unifies REST, WebSocket, and Model Context Protocol (MCP) JSON-RPC 2.0 communication
under standard contracts, enforcing semantic versioning, RFC 8594 deprecation headers,
and RFC 7807 error envelopes.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.interop.deprecation_manager import DeprecationManager
from app.core.interop.errors import COPPERErrorResponse, ErrorCode
from app.core.interop.mcp_adapter import MCPAdapter
from app.core.logger import logger


@dataclass
class GatewayResponse:
    status_code: int
    data: dict[str, Any]
    protocol: str  # "REST" | "WEBSOCKET" | "MCP"
    headers: dict[str, str] = field(default_factory=dict)
    is_error: bool = False
    error_response: COPPERErrorResponse | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "data": self.data,
            "protocol": self.protocol,
            "headers": self.headers,
            "is_error": self.is_error,
        }


class IntegrationGateway:
    """Unified API Gateway coordinating REST, WebSocket, and MCP protocols."""

    def __init__(
        self,
        mcp_adapter: MCPAdapter | None = None,
        deprecation_mgr: DeprecationManager | None = None,
    ):
        self.mcp = mcp_adapter or MCPAdapter()
        self.deprecation = deprecation_mgr or DeprecationManager()
        self._request_counts: dict[str, int] = {"REST": 0, "WEBSOCKET": 0, "MCP": 0}
        self._error_counts: dict[str, int] = {"REST": 0, "WEBSOCKET": 0, "MCP": 0}

    async def dispatch_rest(
        self,
        endpoint_path: str,
        method: str = "POST",
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> GatewayResponse:
        """Processes incoming REST API requests with deprecation governance."""
        self._request_counts["REST"] += 1
        norm_headers = headers or {}
        resp_headers: dict[str, str] = {}

        # 1. Deprecation check
        dep_headers = self.deprecation.record_usage(endpoint_path)
        resp_headers.update(dep_headers)

        # 2. Hard sunset enforcement
        if self.deprecation.is_sunset(endpoint_path):
            self._error_counts["REST"] += 1
            err = COPPERErrorResponse(
                error_code=ErrorCode.SERVICE_UNAVAILABLE,
                message=f"Endpoint '{endpoint_path}' has reached its sunset date and is permanently decommissioned.",
                status_code=410,
                details={"endpoint": endpoint_path, "sunset_info": dep_headers},
            )
            return GatewayResponse(
                status_code=410,
                data=err.to_dict(),
                protocol="REST",
                headers=resp_headers,
                is_error=True,
                error_response=err,
            )

        # 3. Request validation
        if method not in ("GET", "POST", "PUT", "DELETE"):
            self._error_counts["REST"] += 1
            err = COPPERErrorResponse(
                error_code=ErrorCode.INVALID_REQUEST,
                message=f"Unsupported HTTP method: {method}",
                status_code=405,
            )
            return GatewayResponse(
                status_code=405,
                data=err.to_dict(),
                protocol="REST",
                headers=resp_headers,
                is_error=True,
                error_response=err,
            )

        # 4. Standard success dispatch
        return GatewayResponse(
            status_code=200,
            data={
                "status": "success",
                "endpoint": endpoint_path,
                "received_payload": payload or {},
            },
            protocol="REST",
            headers=resp_headers,
            is_error=False,
        )

    async def dispatch_mcp(self, json_rpc_payload: str | dict[str, Any]) -> GatewayResponse:
        """Routes standard Model Context Protocol (MCP) JSON-RPC 2.0 messages."""
        self._request_counts["MCP"] += 1
        mcp_result = await self.mcp.handle_json_rpc(json_rpc_payload)
        is_err = "error" in mcp_result

        if is_err:
            self._error_counts["MCP"] += 1

        return GatewayResponse(
            status_code=200 if not is_err else 400,
            data=mcp_result,
            protocol="MCP",
            headers={"Content-Type": "application/json"},
            is_error=is_err,
        )

    async def dispatch_websocket_frame(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> GatewayResponse:
        """Processes bi-directional WebSocket event frames."""
        self._request_counts["WEBSOCKET"] += 1

        if not event_type:
            self._error_counts["WEBSOCKET"] += 1
            err = COPPERErrorResponse(
                error_code=ErrorCode.INVALID_REQUEST,
                message="WebSocket frame missing 'event_type'",
                status_code=400,
            )
            return GatewayResponse(
                status_code=400,
                data=err.to_dict(),
                protocol="WEBSOCKET",
                is_error=True,
                error_response=err,
            )

        # Standard event envelope echo / acknowledgement
        return GatewayResponse(
            status_code=200,
            data={
                "event_type": event_type,
                "status": "acknowledged",
                "timestamp": time.time(),
                "payload": payload,
            },
            protocol="WEBSOCKET",
            is_error=False,
        )

    def get_gateway_metrics(self) -> dict[str, Any]:
        """Returns request throughput and error totals across protocols."""
        return {
            "total_requests": sum(self._request_counts.values()),
            "by_protocol": dict(self._request_counts),
            "errors": dict(self._error_counts),
        }


integration_gateway = IntegrationGateway()
