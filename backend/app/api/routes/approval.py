"""REST Endpoints for Real-Time Human-in-the-Loop Operator Approval."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.safety.operator_approval_manager import operator_approval_manager
from app.core.logger import logger

router = APIRouter(prefix="/approval", tags=["operator-approval"])


class ApprovalDecisionRequest(BaseModel):
    ticket_id: str = Field(..., description="Unique approval ticket ID")
    approved: bool = Field(..., description="Whether the operator approves the consequential action")
    reason: Optional[str] = Field("", description="Optional operator justification")
    confirmed_by: Optional[str] = Field("operator", description="Operator identity or signature")


class CreateTicketRequest(BaseModel):
    action: str
    target: str
    actor: str = "agent"
    reason: str
    timeout_seconds: Optional[float] = 60.0


@router.get("/tickets")
async def list_pending_tickets():
    """Lists all active pending approval tickets."""
    return {
        "pending_tickets": operator_approval_manager.get_pending_tickets(),
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Retrieves status of a specific approval ticket."""
    ticket = operator_approval_manager.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return ticket


@router.post("/decide")
async def decide_ticket(req: ApprovalDecisionRequest):
    """Resolves an approval ticket, granting or denying permission for waiting execution."""
    success = operator_approval_manager.resolve_ticket(
        ticket_id=req.ticket_id,
        approved=req.approved,
        reason=req.reason or "",
        confirmed_by=req.confirmed_by or "operator",
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to resolve ticket (invalid ID or already decided).")
    
    return {
        "status": "success",
        "ticket_id": req.ticket_id,
        "decision": "approved" if req.approved else "rejected",
    }


@router.post("/request")
async def request_approval(req: CreateTicketRequest):
    """Creates a new approval ticket and triggers real-time WebSocket broadcast."""
    ticket = await operator_approval_manager.create_ticket(
        action=req.action,
        target=req.target,
        actor=req.actor,
        reason=req.reason,
        timeout_seconds=req.timeout_seconds,
    )
    return ticket.to_dict()
