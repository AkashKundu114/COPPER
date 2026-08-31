import uuid
from typing import Any

from app.ai.memory.memory_manager import memory_manager
from app.ai.tools.registry import tool_registry
from app.core.logger import logger
from app.core.temporal import get_current_temporal_context


@tool_registry.tool(
    name="calendar_create",
    description="Create a scheduled calendar event or meeting with a title, target date/time, and duration.",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title or summary of the event."},
            "datetime": {
                "type": "string",
                "description": "Date and time of the event, e.g. '2026-09-01 14:00' or 'tomorrow at 3pm'.",
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Duration in minutes (defaults to 30).",
            },
        },
        "required": ["title", "datetime"],
    },
    return_description="Confirmation of created calendar event with assigned event ID.",
    guardian_level=0,
)
async def calendar_create(title: str, datetime: str, duration_minutes: int = 30) -> dict[str, Any]:
    try:
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        doc_content = f"Calendar Event: {title} on {datetime} (Duration: {duration_minutes}m)"
        await memory_manager.save_document(
            content=doc_content,
            source="calendar",
            metadata={
                "event_id": event_id,
                "title": title,
                "datetime": datetime,
                "duration_minutes": duration_minutes,
                "type": "calendar_event",
            },
        )
        return {
            "status": "success",
            "event_id": event_id,
            "title": title,
            "datetime": datetime,
            "duration_minutes": duration_minutes,
            "message": f"Calendar event '{title}' scheduled for {datetime}.",
        }
    except Exception as e:
        logger.error(f"calendar_create error: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="reminder_set",
    description="Set a temporal reminder or alarm for a specific time or delay with a message.",
    parameters={
        "type": "object",
        "properties": {
            "time": {
                "type": "string",
                "description": "Target reminder time or offset, e.g. '10 minutes', 'tomorrow 9am', '18:00'.",
            },
            "message": {"type": "string", "description": "Reminder text or notification message."},
            "priority": {
                "type": "string",
                "description": "Priority level: 'low', 'medium' (default), or 'high'.",
            },
        },
        "required": ["time", "message"],
    },
    return_description="Confirmation of scheduled reminder.",
    guardian_level=0,
)
async def reminder_set(time: str, message: str, priority: str = "medium") -> dict[str, Any]:
    try:
        reminder_id = f"rem_{uuid.uuid4().hex[:8]}"
        temporal_now = get_current_temporal_context()
        doc_content = f"Reminder [{priority.upper()}]: {message} at {time}"
        await memory_manager.save_document(
            content=doc_content,
            source="reminder",
            metadata={
                "reminder_id": reminder_id,
                "time": time,
                "message": message,
                "priority": priority,
                "type": "reminder",
            },
        )
        return {
            "status": "success",
            "reminder_id": reminder_id,
            "time": time,
            "message": message,
            "priority": priority,
            "temporal_context": temporal_now,
            "confirmation": f"Reminder set for '{time}': {message}",
        }
    except Exception as e:
        logger.error(f"reminder_set error: {e}")
        return {"status": "error", "error": str(e)}
