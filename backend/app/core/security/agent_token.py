"""Cryptographic Agent Identity and Delegation Service.

Implements Zero-Trust Principle 3: "Never trust an agent merely because it belongs to COPPER."
Provides signed, scoped AgentTokens limiting agent capability boundaries.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass
from typing import Any

from app.core.logger import logger
from app.core.security.auth import key_manager


@dataclass
class AgentTokenPayload:
    token_id: str
    agent_id: str
    agent_type: str
    allowed_tools: list[str]
    max_steps: int
    issued_at: float
    expires_at: float
    session_id: str | None = None
    parent_agent_id: str | None = None


class AgentTokenService:
    """Issues and verifies tamper-evident cryptographically signed AgentTokens."""

    def __init__(self):
        self._key_manager = key_manager

    def _get_signing_key(self) -> bytes:
        return self._key_manager.get_or_create_operator_key().encode("utf-8")

    def issue_token(
        self,
        agent_id: str,
        agent_type: str,
        allowed_tools: list[str],
        ttl_seconds: int = 300,
        max_steps: int = 5,
        session_id: str | None = None,
        parent_agent_id: str | None = None,
    ) -> str:
        """Issues an HMAC-SHA256 signed capability token for an agent."""
        now = time.time()
        token_id = hashlib.sha256(f"{agent_id}:{now}".encode("utf-8")).hexdigest()[:16]
        payload = AgentTokenPayload(
            token_id=token_id,
            agent_id=agent_id,
            agent_type=agent_type,
            allowed_tools=list(allowed_tools),
            max_steps=max_steps,
            issued_at=now,
            expires_at=now + ttl_seconds,
            session_id=session_id,
            parent_agent_id=parent_agent_id,
        )

        payload_bytes = json.dumps(asdict(payload), separators=(",", ":")).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")

        sig = hmac.new(self._get_signing_key(), b64_payload.encode("utf-8"), hashlib.sha256).digest()
        b64_sig = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")

        return f"agtok.{b64_payload}.{b64_sig}"

    def verify_token(self, token_str: str) -> AgentTokenPayload | None:
        """Verifies an AgentToken's signature and expiration."""
        if not token_str or not token_str.startswith("agtok."):
            return None

        parts = token_str.split(".")
        if len(parts) != 3:
            return None

        _, b64_payload, b64_sig = parts

        expected_sig = hmac.new(self._get_signing_key(), b64_payload.encode("utf-8"), hashlib.sha256).digest()
        expected_b64_sig = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")

        if not hmac.compare_digest(b64_sig, expected_b64_sig):
            logger.warning("[Security] AgentToken signature verification failed.")
            return None

        try:
            # Add padding back if necessary
            pad = 4 - (len(b64_payload) % 4)
            if pad != 4:
                b64_payload += "=" * pad
            raw_json = base64.urlsafe_b64decode(b64_payload.encode("utf-8")).decode("utf-8")
            data = json.loads(raw_json)

            payload = AgentTokenPayload(
                token_id=data["token_id"],
                agent_id=data["agent_id"],
                agent_type=data["agent_type"],
                allowed_tools=data.get("allowed_tools", []),
                max_steps=data.get("max_steps", 5),
                issued_at=data["issued_at"],
                expires_at=data["expires_at"],
                session_id=data.get("session_id"),
                parent_agent_id=data.get("parent_agent_id"),
            )

            if time.time() > payload.expires_at:
                logger.warning(f"[Security] AgentToken {payload.token_id} expired.")
                return None

            return payload
        except Exception as e:
            logger.error(f"[Security] AgentToken deserialization error: {e}")
            return None


agent_token_service = AgentTokenService()
