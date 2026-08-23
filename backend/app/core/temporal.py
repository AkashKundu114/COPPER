import json
from datetime import datetime
from pathlib import Path

from app.core.logger import logger

REMINDERS_FILE = Path(__file__).parent.parent.parent / "data" / "reminders.json"

def get_current_temporal_context() -> str:
    now = datetime.now().astimezone()
    date_str = now.strftime("%A, %B %d, %Y")
    time_12 = now.strftime("%I:%M:%S %p")
    time_24 = now.strftime("%H:%M:%S")
    tz_str = now.strftime("%Z (UTC%z)")

    return (
        f"[LIVE SYSTEM CLOCK & TEMPORAL CONTEXT]\n"
        f"• Current Local Time: {time_12} ({time_24})\n"
        f"• Current Date: {date_str}\n"
        f"• Local Timezone: {tz_str}\n"
        f"• CRITICAL: Base all duration, alarm, task scheduling, and time calculations strictly on this live clock."
    )

def load_reminders() -> list[dict]:
    try:
        if REMINDERS_FILE.exists():
            with open(REMINDERS_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading reminders: {e}")
    return []

def save_reminder(title: str, target_time_str: str, duration_mins: int = 0) -> dict:
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    reminders = load_reminders()
    item = {
        "id": f"rem-{int(datetime.now().timestamp())}",
        "title": title,
        "target_time": target_time_str,
        "duration_mins": duration_mins,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    reminders.append(item)
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving reminder: {e}")
    return item
