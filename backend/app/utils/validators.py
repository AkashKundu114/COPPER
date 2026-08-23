def validate_message(message: str) -> tuple[bool, str]:
    cleaned = message.strip()
    if not cleaned:
        return (False, "Message content cannot be empty.")
    if len(cleaned) > 100000:
        return (False, "Message exceeds maximum allowed length (100,000 characters).")
    return (True, "")
