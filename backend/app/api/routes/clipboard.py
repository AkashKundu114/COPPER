from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.ai.ambient.clipboard_monitor import clipboard_monitor
from app.ai.ambient.clipboard_processor import clipboard_processor
from app.core.logger import logger

router = APIRouter(prefix="/clipboard", tags=["clipboard"])


@router.get("/history")
async def get_history(skip: int = 0, limit: int = 50):
    """Get recent clipboard entries."""
    history = list(clipboard_monitor.history)
    end = skip + limit
    return history[skip:end]


@router.get("/history/{entry_id}")
async def get_entry(entry_id: str):
    """Get a specific clipboard entry by ID."""
    for entry in clipboard_monitor.history:
        if entry.id == entry_id:
            return entry
    raise HTTPException(status_code=404, detail="Entry not found")


@router.get("/current")
async def get_current_entry():
    """Get the most recent clipboard entry."""
    if not clipboard_monitor.history:
        raise HTTPException(status_code=404, detail="Clipboard history is empty")
    return clipboard_monitor.history[0]


@router.post("/process/{entry_id}")
async def process_entry(entry_id: str):
    """Trigger processing on a specific entry."""
    for entry in clipboard_monitor.history:
        if entry.id == entry_id:
            result = clipboard_processor.process_entry(entry)
            return {"status": "success", "entry": entry}
    raise HTTPException(status_code=404, detail="Entry not found")


@router.delete("/history")
async def clear_history():
    """Clear clipboard history."""
    clipboard_monitor.history.clear()
    return {"status": "success", "message": "Clipboard history cleared"}
