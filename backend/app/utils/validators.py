import re
from datetime import datetime
from typing import Optional


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_datetime_string(dt_str: str) -> Optional[datetime]:
    try:
        from app.utils.helpers import parse_datetime
        return parse_datetime(dt_str)
    except ValueError:
        return None


def is_safe_path(path: str) -> bool:
    """Prevent path traversal attacks."""
    return ".." not in path and not path.startswith("/etc") and not path.startswith("/sys")


def validate_cron_expression(expr: str) -> bool:
    """Basic cron expression validation (5 fields)."""
    parts = expr.strip().split()
    return len(parts) == 5


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Remove potentially dangerous characters and trim length."""
    text = text.strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text[:max_length]


def validate_message(message: str) -> tuple[bool, str]:
    if not message or not message.strip():
        return False, "Message cannot be empty"
    if len(message) > 32000:
        return False, "Message too long (max 32000 characters)"
    return True, ""


def validate_session_id(session_id: str) -> bool:
    pattern = r"^[a-f0-9\-]{36}$"
    return bool(re.match(pattern, session_id))
