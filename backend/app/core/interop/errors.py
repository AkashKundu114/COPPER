"""Standardized API Error Envelope and Canonical Error Codes for C.O.P.P.E.R.

RFC 7807 Problem Details compliant error structures ensuring consistent,
attributable, and machine-parsable error reporting across all endpoints and agents.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    # System & Runtime Errors (1000-1999)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"

    # Security & Policy Errors (2000-2999)
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    GUARDIAN_SAFETY_INTERVENTION = "GUARDIAN_SAFETY_INTERVENTION"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SSRF_BLOCKED = "SSRF_BLOCKED"

    # Agent & Tool Contract Errors (3000-3999)
    INVALID_REQUEST = "INVALID_REQUEST"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    UNKNOWN_AGENT = "UNKNOWN_AGENT"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_IDEMPOTENCY_CONFLICT = "TOOL_IDEMPOTENCY_CONFLICT"
    TOOL_CANCELLED = "TOOL_CANCELLED"

    # Resource & Budget Errors (4000-4999)
    VRAM_EXHAUSTION = "VRAM_EXHAUSTION"
    TOKEN_BUDGET_EXCEEDED = "TOKEN_BUDGET_EXCEEDED"
    STORAGE_QUOTA_EXCEEDED = "STORAGE_QUOTA_EXCEEDED"


@dataclass
class COPPERErrorResponse:
    """Canonical RFC 7807 Problem Details representation."""
    error_code: ErrorCode
    message: str
    status_code: int = 500
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["error_code"] = self.error_code.value
        return data
