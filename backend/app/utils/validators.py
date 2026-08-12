from fastapi import HTTPException


def validate_message(message: str) -> str:
    cleaned = message.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")
    if len(cleaned) > 20000:
        raise HTTPException(status_code=400, detail="Message exceeds maximum allowed length.")
    return cleaned
