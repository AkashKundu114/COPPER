def validate_message(message: str) -> tuple[bool, str]:
    if not isinstance(message, str):
        return (False, "Message content must be a string.")

    cleaned = message.strip()
    if not cleaned:
        return (False, "Message content cannot be empty.")
    if len(cleaned) > 20000:
        return (False, "Message exceeds maximum allowed length (20,000 characters).")
    return (True, "")
