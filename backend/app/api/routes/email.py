from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.ai.ambient.email_agent import email_agent

router = APIRouter(prefix="/email", tags=["email"])

class EmailConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True

@router.post("/configure")
async def configure_email(config: EmailConfig):
    email_agent.configure(config.host, config.port, config.username, config.password, config.use_ssl)
    return {"status": "configured"}

@router.get("/configured")
async def is_configured():
    return {"configured": email_agent.is_configured()}

@router.post("/fetch")
async def fetch_emails(limit: int = 20):
    emails = await email_agent.fetch_emails(limit)
    return {"fetched": len(emails), "emails": emails}

@router.get("/inbox")
async def get_inbox(priority: Optional[str] = None):
    return email_agent.get_inbox(priority)

@router.get("/inbox/{email_id}")
async def get_email(email_id: str):
    emails = email_agent.get_inbox()
    for e in emails:
        if e.email_id == email_id:
            return e
    raise HTTPException(status_code=404, detail="Email not found")

@router.post("/draft/{email_id}")
async def draft_response(email_id: str):
    draft = await email_agent.draft_response(email_id)
    return {"draft": draft}

@router.get("/drafts")
async def get_drafts():
    return email_agent.get_drafts()

@router.post("/draft/{email_id}/approve")
async def approve_draft(email_id: str):
    return email_agent.approve_draft(email_id)

@router.post("/draft/{email_id}/reject")
async def reject_draft(email_id: str):
    return email_agent.reject_draft(email_id)
