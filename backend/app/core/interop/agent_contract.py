"""Standardized Agent Invocation and Communication Contracts for C.O.P.P.E.R.

Defines canonical Pydantic request and response schemas, capability manifests,
and execution metadata for internal and cross-agent communication.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.core.constants import AgentType
from app.core.interop.errors import COPPERErrorResponse


class ResponseStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    CHALLENGED = "CHALLENGED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass
class AgentMetadata:
    agent_id: str
    model_name: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tools_called: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class AgentRequest:
    task: str
    session_id: str = "default"
    target_agent: AgentType = AgentType.CHAT
    caller: str = "user"
    context: dict[str, Any] = field(default_factory=dict)
    memory_context: str = ""
    timeout_s: float = 60.0
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["target_agent"] = self.target_agent.value
        return data


@dataclass
class AgentResponse:
    request_id: str
    status: ResponseStatus
    content: str
    metadata: AgentMetadata
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    error: COPPERErrorResponse | None = None
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        if self.error:
            data["error"] = self.error.to_dict()
        return data


@dataclass(frozen=True)
class AgentCapability:
    name: str
    description: str
    supported_modalities: list[str]  # e.g., ["text", "code", "image", "audio"]
    authorized_tools: list[str]
    max_context_window: int = 8192
    supports_streaming: bool = True
