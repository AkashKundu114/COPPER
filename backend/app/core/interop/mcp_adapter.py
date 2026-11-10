"""Model Context Protocol (MCP) JSON-RPC 2.0 Server Adapter for C.O.P.P.E.R.

Exposes COPPER tools to standard MCP clients (Claude Desktop, VS Code, Antigravity)
using the standardized JSON-RPC 2.0 protocol over stdio / SSE.
"""

from __future__ import annotations

import json
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.interop.tool_contract import tool_contract_wrapper
from app.core.logger import logger


class MCPAdapter:
    """Bridges COPPER tools to the Model Context Protocol (MCP) specification."""

    def __init__(self, registry=tool_registry):
        self.registry = registry

    async def handle_json_rpc(self, request_payload: str | dict[str, Any]) -> dict[str, Any]:
        """Processes an incoming JSON-RPC 2.0 MCP request."""
        if isinstance(request_payload, str):
            try:
                data = json.loads(request_payload)
            except Exception as e:
                return self._error_response(None, -32700, f"Parse error: {str(e)}")
        else:
            data = request_payload

        req_id = data.get("id")
        method = data.get("method", "")
        params = data.get("params", {})

        if data.get("jsonrpc") != "2.0":
            return self._error_response(req_id, -32600, "Invalid Request: jsonrpc must be '2.0'")

        # Dispatch method
        if method == "tools/list":
            return await self._handle_tools_list(req_id)
        elif method == "tools/call":
            return await self._handle_tools_call(req_id, params)
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        else:
            return self._error_response(req_id, -32601, f"Method not found: '{method}'")

    async def _handle_tools_list(self, req_id: Any) -> dict[str, Any]:
        """MCP tools/list handler."""
        tools_list = []
        for t in self.registry.list_tools():
            tools_list.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.parameters,
                }
            )
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": tools_list,
            },
        }

    async def _handle_tools_call(self, req_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """MCP tools/call handler."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            return self._error_response(req_id, -32602, "Invalid params: 'name' is required")

        tool = self.registry.get(tool_name)
        if not tool:
            return self._error_response(req_id, -32602, f"Unknown tool: '{tool_name}'")

        # Execute through hardened contract wrapper
        res = await tool_contract_wrapper.execute_contract(tool, arguments)

        if not res.success:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {res.error.message if res.error else 'Tool execution failed'}",
                        }
                    ],
                    "isError": True,
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(res.output, default=str) if isinstance(res.output, (dict, list)) else str(res.output),
                    }
                ],
                "isError": False,
            },
        }

    @staticmethod
    def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": message,
            },
        }


mcp_adapter = MCPAdapter()
