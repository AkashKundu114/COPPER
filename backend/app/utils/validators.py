from typing import Tuple

def validate_message(message: str) -> Tuple[bool, str]:
    cleaned = message.strip()
    if not cleaned:
        return (False, 'Message content cannot be empty.')
    if len(cleaned) > 20000:
        return (False, 'Message exceeds maximum allowed length.')
    return (True, '')