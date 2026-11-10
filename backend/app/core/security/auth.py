"""Zero-Trust Security & Identity Architecture for COPPER.

Provides authentication, identity verification, and credential handling
under the COPPER local-first operating model.
"""

from __future__ import annotations

import hmac
import os
import secrets
import stat
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.logger import logger

OPERATOR_KEY_FILENAME = "copper_operator.key"
_TOKEN_HEADER_API_KEY = "X-API-Key"
_TOKEN_HEADER_AGENT = "X-Agent-Token"


class PrincipalType(str, Enum):
    OPERATOR = "operator"
    AGENT = "agent"
    SYSTEM = "system"
    ANONYMOUS = "anonymous"


@dataclass
class Principal:
    """Represents an authenticated entity within the COPPER trust perimeter."""

    id: str
    principal_type: PrincipalType
    role: str
    scopes: set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return self.principal_type != PrincipalType.ANONYMOUS


class KeyManager:
    """Manages the host-local cryptographic root key for operator access.
    
    Generates a cryptographically strong 256-bit entropy key stored in a local
    file with restricted file permissions (0600 on POSIX).
    """

    def __init__(self, key_path: Path | None = None):
        if key_path is None:
            data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.key_path = data_dir / OPERATOR_KEY_FILENAME
        else:
            self.key_path = key_path
        self._master_key: str | None = None

    def get_or_create_operator_key(self) -> str:
        """Retrieves existing operator key or provisions a new one."""
        if self._master_key:
            return self._master_key

        env_key = os.environ.get("COPPER_API_KEY")
        if env_key and env_key.strip():
            self._master_key = env_key.strip()
            return self._master_key

        if self.key_path.exists():
            try:
                with open(self.key_path, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                if len(key) >= 32:
                    self._master_key = key
                    return self._master_key
            except Exception as e:
                logger.warning(f"[Security] Failed reading existing key file: {e}")

        new_key = f"copper_op_{secrets.token_urlsafe(32)}"
        try:
            with open(self.key_path, "w", encoding="utf-8") as f:
                f.write(new_key)
            if os.name != "nt":
                try:
                    os.chmod(self.key_path, stat.S_IRUSR | stat.S_IWUSR)
                except OSError:
                    pass
            self._master_key = new_key
            logger.info(f"[Security] Provisioned new operator key at {self.key_path}")
        except Exception as e:
            logger.error(f"[Security] Failed persisting operator key to disk: {e}")
            self._master_key = new_key

        return self._master_key

    def verify_key(self, candidate_key: str) -> bool:
        """Constant-time verification of candidate key."""
        if not candidate_key:
            return False
        expected = self.get_or_create_operator_key()
        return hmac.compare_digest(candidate_key.strip(), expected.strip())


key_manager = KeyManager()

_bearer_security = HTTPBearer(auto_error=False)


def authenticate_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_security),
) -> Principal:
    """FastAPI dependency to authenticate and resolve the current Principal.
    
    Zero-Trust enforcement:
    1. Checks X-API-Key header against KeyManager.
    2. Checks Authorization: Bearer <token> against KeyManager.
    3. If COPPER_DEMO=1 and no credentials provided, resolves to limited demo operator.
    4. Otherwise, rejects with 401 Unauthorized.
    """
    api_key_header = request.headers.get(_TOKEN_HEADER_API_KEY)
    token = None

    if api_key_header:
        token = api_key_header.strip()
    elif credentials and credentials.credentials:
        token = credentials.credentials.strip()

    if token:
        if key_manager.verify_key(token):
            return Principal(
                id="local_operator",
                principal_type=PrincipalType.OPERATOR,
                role="admin",
                scopes={"*"},
            )
        # Check if it matches an internal agent token
        from app.core.security.agent_token import agent_token_service

        agent_token_data = agent_token_service.verify_token(token)
        if agent_token_data:
            return Principal(
                id=agent_token_data.agent_id,
                principal_type=PrincipalType.AGENT,
                role="agent",
                scopes=set(agent_token_data.allowed_tools),
                metadata={"agent_type": agent_token_data.agent_type},
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In standalone demo or test environment where auth is optionally bypassed if configured
    if getattr(settings, "COPPER_DEMO", False):
        return Principal(
            id="demo_operator",
            principal_type=PrincipalType.OPERATOR,
            role="operator",
            scopes={"*"},
        )

    # Public unauthenticated routes
    path = request.url.path
    if path in {"/", "/health", "/docs", "/openapi.json", "/redoc"} or path.startswith("/static"):
        return Principal(
            id="anonymous",
            principal_type=PrincipalType.ANONYMOUS,
            role="read_only",
            scopes={"read"},
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide 'Authorization: Bearer <key>' or 'X-API-Key' header.",
        headers={"WWW-Authenticate": "Bearer"},
    )
