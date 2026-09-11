from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.ambient.meeting_intelligence import meeting_intelligence

router = APIRouter(prefix="/meetings", tags=["meetings"])


class StartMeetingRequest(BaseModel):
    title: str = "Untitled Meeting"


@router.post("/start")
async def start_recording(request: StartMeetingRequest):
    """Start recording a new meeting."""
    record = meeting_intelligence.start_recording(title=request.title)
    return {"status": "success", "meeting_id": record.meeting_id, "record": record}


@router.post("/{meeting_id}/stop")
async def stop_recording(meeting_id: str):
    """Stop recording and trigger processing pipeline."""
    try:
        record = meeting_intelligence.stop_recording(meeting_id)
        return {"status": "success", "meeting_id": meeting_id, "record": record}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("")
async def list_meetings(limit: int = 20):
    """List all meetings."""
    return {"meetings": meeting_intelligence.list_meetings(limit=limit)}


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get meeting details including transcript and notes."""
    record = meeting_intelligence.get_meeting(meeting_id)
    if not record:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting": record}


@router.get("/{meeting_id}/notes")
async def get_meeting_notes(meeting_id: str):
    """Get only the structured notes for a meeting."""
    record = meeting_intelligence.get_meeting(meeting_id)
    if not record:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"structured_notes": record.structured_notes}


@router.get("/{meeting_id}/tasks")
async def get_meeting_tasks(meeting_id: str):
    """Get the auto-created tasks for a meeting."""
    record = meeting_intelligence.get_meeting(meeting_id)
    if not record:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"auto_tasks_created": record.auto_tasks_created}
