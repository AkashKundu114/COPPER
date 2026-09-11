from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.ai.os_integration.notification_filter import notification_filter

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationCreate(BaseModel):
    source: str
    title: str
    message: str

class NotificationResponse(BaseModel):
    id: str
    source: str
    title: str
    message: str
    timestamp: str
    category: str
    status: str

@router.post("", response_model=NotificationResponse)
async def create_notification(data: NotificationCreate):
    notif = notification_filter.post_notification(data.source, data.title, data.message)
    return notif

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(status: Optional[str] = None):
    return notification_filter.get_notifications(status=status)

@router.get("/digest", response_model=Dict[str, Any])
async def get_digest():
    return notification_filter.generate_digest()

@router.post("/{id}/read")
async def mark_read(id: str):
    notification_filter.mark_delivered(id)
    return {"status": "success"}
