"""Hardened Tool Execution Contract Wrapper for C.O.P.P.E.R.

Provides standardized input/output schema validation, execution timeouts,
async cancellation support, and idempotency key caching for tool invocations.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from app.ai.tools.registry import BaseTool
from app.core.interop.errors import COPPERErrorResponse, ErrorCode
from app.core.logger import logger


@dataclass
class ContractExecutionResult:
    tool_name: str
    output: Any
    success: bool
    execution_time_ms: float
    error: COPPERErrorResponse | None = None
    idempotent_cached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "output": self.output,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error.to_dict() if self.error else None,
            "idempotent_cached": self.idempotent_cached,
            "metadata": self.metadata,
        }


class ToolContractWrapper:
    """Enforces execution boundaries, timeouts, and idempotency on tools."""

    def __init__(self, default_timeout_seconds: float = 30.0):
        self.default_timeout = default_timeout_seconds
        self._idempotency_cache: dict[str, Any] = {}

    def compute_idempotency_key(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Computes deterministic idempotency fingerprint for a tool invocation."""
        raw = f"{tool_name}:{json.dumps(arguments, sort_keys=True, default=str)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def execute_contract(
        self,
        tool: BaseTool,
        arguments: dict[str, Any],
        timeout_seconds: float | None = None,
        idempotency_key: str | None = None,
    ) -> ContractExecutionResult:
        """Executes a tool within strict contract boundaries."""
        t_start = time.perf_counter()
        timeout = timeout_seconds or self.default_timeout

        # 1. Input Schema Validation
        valid, validation_err = tool.validate_args(arguments)
        if not valid:
            dur = (time.perf_counter() - t_start) * 1000.0
            return ContractExecutionResult(
                tool_name=tool.name,
                output=None,
                success=False,
                execution_time_ms=round(dur, 2),
                error=COPPERErrorResponse(
                    error_code=ErrorCode.SCHEMA_VALIDATION_ERROR,
                    message=f"Contract input validation failed: {validation_err}",
                    status_code=400,
                ),
            )

        # 2. Check Idempotency Cache
        eff_key = idempotency_key or self.compute_idempotency_key(tool.name, arguments)
        if eff_key in self._idempotency_cache:
            dur = (time.perf_counter() - t_start) * 1000.0
            cached_output = self._idempotency_cache[eff_key]
            logger.debug(f"[ToolContract] Returning cached idempotent output for {tool.name} (Key: {eff_key[:12]})")
            return ContractExecutionResult(
                tool_name=tool.name,
                output=cached_output,
                success=True,
                execution_time_ms=round(dur, 2),
                idempotent_cached=True,
            )

        # 3. Timed Execution with Cancellation Handling
        try:
            output = await asyncio.wait_for(tool.execute(**arguments), timeout=timeout)
            dur = (time.perf_counter() - t_start) * 1000.0

            # Cache successful idempotent output
            self._idempotency_cache[eff_key] = output
            if len(self._idempotency_cache) > 500:
                self._idempotency_cache.pop(next(iter(self._idempotency_cache)))

            return ContractExecutionResult(
                tool_name=tool.name,
                output=output,
                success=True,
                execution_time_ms=round(dur, 2),
            )

        except asyncio.TimeoutError:
            dur = (time.perf_counter() - t_start) * 1000.0
            logger.warning(f"[ToolContract] Tool '{tool.name}' timed out after {timeout}s")
            return ContractExecutionResult(
                tool_name=tool.name,
                output=None,
                success=False,
                execution_time_ms=round(dur, 2),
                error=COPPERErrorResponse(
                    error_code=ErrorCode.TIMEOUT,
                    message=f"Tool '{tool.name}' exceeded bounded timeout of {timeout}s",
                    status_code=504,
                    retryable=True,
                ),
            )

        except asyncio.CancelledError:
            dur = (time.perf_counter() - t_start) * 1000.0
            logger.info(f"[ToolContract] Tool '{tool.name}' execution cancelled by caller")
            return ContractExecutionResult(
                tool_name=tool.name,
                output=None,
                success=False,
                execution_time_ms=round(dur, 2),
                error=COPPERErrorResponse(
                    error_code=ErrorCode.TOOL_CANCELLED,
                    message=f"Tool '{tool.name}' execution was cancelled",
                    status_code=499,
                    retryable=False,
                ),
            )

        except Exception as e:
            dur = (time.perf_counter() - t_start) * 1000.0
            logger.error(f"[ToolContract] Tool '{tool.name}' threw exception: {e}")
            return ContractExecutionResult(
                tool_name=tool.name,
                output=None,
                success=False,
                execution_time_ms=round(dur, 2),
                error=COPPERErrorResponse(
                    error_code=ErrorCode.TOOL_EXECUTION_FAILED,
                    message=f"Execution error in tool '{tool.name}': {str(e)}",
                    status_code=500,
                ),
            )


tool_contract_wrapper = ToolContractWrapper()
