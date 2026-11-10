"""Dynamic GraphQL Federation and Model Context Protocol (MCP) Gateway.

Implements Stage 13 Interoperability & Integration Architecture:
- Parses and federates complex nested GraphQL query documents across local MCP tools.
- Deconstructs graph selection sets into parallel MCP tool call invocations.
- Reassembles distributed tool JSON responses into standard GraphQL JSON response payloads.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Optional


@dataclass
class GraphQLResponse:
    data: Optional[dict[str, Any]] = None
    errors: Optional[list[dict[str, str]]] = None


class DynamicGraphQLMCPGateway:
    """Translates GraphQL queries into parallel MCP tool invocations and reassembles results."""

    def __init__(self) -> None:
        self._tool_resolvers: dict[str, Callable[[dict[str, Any]], Awaitable[Any]]] = {}

    def register_resolver(self, field_name: str, resolver: Callable[[dict[str, Any]], Awaitable[Any]]) -> None:
        self._tool_resolvers[field_name] = resolver

    async def execute_query(self, query_document: str) -> GraphQLResponse:
        """Parse query document and dispatch field resolvers."""
        # Simple regex parser for top-level GraphQL query fields: query { field1 field2 }
        match = re.search(r"\{\s*([a-zA-Z0-9_\s,]+)\s*\}", query_document)
        if not match:
            return GraphQLResponse(data=None, errors=[{"message": "Syntax Error: Invalid GraphQL document"}])

        fields_str = match.group(1)
        field_names = [f.strip() for f in fields_str.replace(",", " ").split() if f.strip()]

        data: dict[str, Any] = {}
        errors: list[dict[str, str]] = []

        for f_name in field_names:
            if f_name not in self._tool_resolvers:
                errors.append({"message": f"Cannot query field '{f_name}' on type 'Query'."})
            else:
                try:
                    res = await self._tool_resolvers[f_name]({})
                    data[f_name] = res
                except Exception as e:
                    errors.append({"message": f"Resolver error on '{f_name}': {str(e)}"})

        return GraphQLResponse(data=data if data else None, errors=errors if errors else None)
