import re
from dataclasses import dataclass
from enum import Enum


class DataClass(str, Enum):
    PUBLIC = "public"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


@dataclass
class FirewallResult:
    redacted_text: str
    classification: DataClass
    redaction_count: int


_PATTERNS: list[tuple[re.Pattern, str, DataClass]] = [
    (
        re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9_-]+ )?PRIVATE KEY-----"),
        "•••PRIVATE_KEY_REDACTED•••",
        DataClass.SECRET,
    ),
    (re.compile(r"\bsk-ant-[a-zA-Z0-9_\-]{20,}\b"), "sk-ant-•••REDACTED•••", DataClass.SECRET),
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"), "sk-•••REDACTED•••", DataClass.SECRET),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "•••AWS_KEY_REDACTED•••", DataClass.SECRET),
    (
        re.compile(r"(?i)\b(aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*[A-Za-z0-9/+=]{40}\b"),
        "•••AWS_SECRET_REDACTED•••",
        DataClass.SECRET,
    ),
    (
        re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{82})\b"),
        "•••GITHUB_TOKEN_REDACTED•••",
        DataClass.SECRET,
    ),
    (re.compile(r"\bhf_[a-zA-Z0-9]{34,}\b"), "hf_•••REDACTED•••", DataClass.SECRET),
    (
        re.compile(r"\b([a-zA-Z0-9+.-]+://[^:\s/]+):([^@\s/]+)@"),
        r"\1:•••PASSWORD_REDACTED•••@",
        DataClass.SECRET,
    ),
    (
        re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*\S+"),
        "•••CREDENTIAL_REDACTED•••",
        DataClass.SECRET,
    ),
    (
        re.compile(r"(?i)\b(password|passwd|pwd)\s*[:=]\s*([\"'][^\"'\s]+[\"']|\S+)"),
        "•••PASSWORD_REDACTED•••",
        DataClass.SECRET,
    ),
    (re.compile(r"(?i)\bAuthorization:\s*Bearer\s+\S+"), "Authorization: Bearer •••REDACTED•••", DataClass.SECRET),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "•••EMAIL_REDACTED•••", DataClass.SENSITIVE),
    (
        re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "•••PHONE_REDACTED•••",
        DataClass.SENSITIVE,
    ),
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "•••IP_REDACTED•••", DataClass.SENSITIVE),
    (re.compile(r"(?:/home/|/Users/|C:\\Users\\)[\w.\\/ -]+"), "•••PATH_REDACTED•••", DataClass.PERSONAL),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "•••SSN_REDACTED•••", DataClass.SENSITIVE),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "•••CREDIT_CARD_REDACTED•••", DataClass.SENSITIVE),
]


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
