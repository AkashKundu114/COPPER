"""Authentication and Identity API routes for COPPER Zero-Trust Architecture."""

from fastapi import APIRouter, Depends, HTTPException, Security, status
from pydantic import BaseModel, Field

from app.core.security.access_control import Permission, access_controller
from app.core.security.agent_token import agent_token_service
from app.core.security.auth import Principal, authenticate_request, key_manager

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenVerifyRequest(BaseModel):
    token: str = Field(..., description="API key or AgentToken to verify")


class AgentTokenRequest(BaseModel):
    agent_id: str
    agent_type: str
    allowed_tools: list[str]
    ttl_seconds: int = 300
    max_steps: int = 5


@router.get("/me")
async def get_current_principal(principal: Principal = Depends(authenticate_request)):
    """Returns the authenticated principal and its granted scopes."""
    return {
        "status": "authenticated",
        "id": principal.id,
        "type": principal.principal_type.value,
        "role": principal.role,
        "scopes": list(principal.scopes),
    }


@router.post("/verify")
async def verify_credential(req: TokenVerifyRequest):
    """Verifies an API key or AgentToken without authenticating the session."""
    raw_tok = req.token.strip()
    if raw_tok.startswith("agtok."):
        payload = agent_token_service.verify_token(raw_tok)
        if payload:
            return {
                "valid": True,
                "type": "agent_token",
                "agent_id": payload.agent_id,
                "allowed_tools": payload.allowed_tools,
                "expires_at": payload.expires_at,
            }
        return {"valid": False, "type": "agent_token", "error": "Invalid or expired agent token"}

    is_valid = key_manager.verify_key(raw_tok)
    return {"valid": is_valid, "type": "operator_key"}


@router.post("/agent-token")
async def issue_agent_token(
    req: AgentTokenRequest,
    principal: Principal = Depends(authenticate_request),
):
    """Issues a cryptographically signed AgentToken. Requires OPERATOR or ADMIN role."""
    is_auth, err = access_controller.is_authorized(principal, Permission.AGENT_ACTIVATE)
    if not is_auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied to issue AgentToken: {err}",
        )

    token = agent_token_service.issue_token(
        agent_id=req.agent_id,
        agent_type=req.agent_type,
        allowed_tools=req.allowed_tools,
        ttl_seconds=req.ttl_seconds,
        max_steps=req.max_steps,
    )
    return {
        "status": "success",
        "agent_id": req.agent_id,
        "token": token,
        "ttl_seconds": req.ttl_seconds,
    }
