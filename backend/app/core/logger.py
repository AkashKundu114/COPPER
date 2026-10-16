import logging
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REDACTION_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE), "[REDACTED_AWS_KEY]"),
    (
        re.compile(
            r"(password|passwd|pwd|secret|api_key|access_token)\s*[:=]\s*['\"]?([^'\"\s,]+)['\"]?",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            re.IGNORECASE,
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
]


class RedactingFilter(logging.Filter):
    """Intercepts and redacts secrets, tokens, passwords, and private keys from all log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, repl in REDACTION_PATTERNS:
                msg = pattern.sub(repl, msg)
            record.msg = msg
        if record.args:
            if isinstance(record.args, dict):
                clean_args = {}
                for k, v in record.args.items():
                    if isinstance(v, str):
                        for pattern, repl in REDACTION_PATTERNS:
                            v = pattern.sub(repl, v)
                    clean_args[k] = v
                record.args = clean_args
            elif isinstance(record.args, tuple):
                clean_list = []
                for v in record.args:
                    if isinstance(v, str):
                        for pattern, repl in REDACTION_PATTERNS:
                            v = pattern.sub(repl, v)
                    clean_list.append(v)
                record.args = tuple(clean_list)
        return True


def get_logger(name: str = "copper") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S"))
    handler.addFilter(RedactingFilter())
    logger.addHandler(handler)
    return logger


logger = get_logger()
