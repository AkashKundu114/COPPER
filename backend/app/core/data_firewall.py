import re
from dataclasses import dataclass
from enum import Enum

class DataClass(str, Enum):
    PUBLIC = 'public'
    PERSONAL = 'personal'
    SENSITIVE = 'sensitive'
    SECRET = 'secret'

@dataclass
class FirewallResult:
    redacted_text: str
    classification: DataClass
    redaction_count: int
_PATTERNS: list[tuple[re.Pattern, str, DataClass]] = [(re.compile('sk-[a-zA-Z0-9]{20,}'), 'sk-•••REDACTED•••', DataClass.SECRET), (re.compile('(?i)\\b(api[_-]?key|access[_-]?token|secret[_-]?key)\\s*[:=]\\s*\\S+'), '•••CREDENTIAL_REDACTED•••', DataClass.SECRET), (re.compile('(?i)\\bAuthorization:\\s*Bearer\\s+\\S+'), 'Authorization: Bearer •••REDACTED•••', DataClass.SECRET), (re.compile('\\b[\\w.+-]+@[\\w-]+\\.[\\w.-]+\\b'), '•••EMAIL_REDACTED•••', DataClass.SENSITIVE), (re.compile('\\b(?:\\+?\\d{1,3}[-.\\s]?)?\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b'), '•••PHONE_REDACTED•••', DataClass.SENSITIVE), (re.compile('\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b'), '•••IP_REDACTED•••', DataClass.SENSITIVE), (re.compile('(?:/home/|/Users/|C:\\\\Users\\\\)[\\w.\\\\/ -]+'), '•••PATH_REDACTED•••', DataClass.PERSONAL), (re.compile('\\b\\d{3}-\\d{2}-\\d{4}\\b'), '•••SSN_REDACTED•••', DataClass.SENSITIVE), (re.compile('\\b(?:\\d[ -]*?){13,19}\\b'), '•••CREDIT_CARD_REDACTED•••', DataClass.SENSITIVE)]

def classify_and_redact(text: str) -> FirewallResult:
    severity_order = [DataClass.PUBLIC, DataClass.PERSONAL, DataClass.SENSITIVE, DataClass.SECRET]
    worst = DataClass.PUBLIC
    redaction_count = 0
    result_text = text
    for pattern, replacement, classification in _PATTERNS:
        result_text, n = pattern.subn(replacement, result_text)
        if n:
            redaction_count += n
            if severity_order.index(classification) > severity_order.index(worst):
                worst = classification
    return FirewallResult(redacted_text=result_text, classification=worst, redaction_count=redaction_count)

def redact(text: str) -> str:
    return classify_and_redact(text).redacted_text