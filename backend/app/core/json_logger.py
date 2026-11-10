"""Structured JSON Logging Formatter and Multi-Sink Logger for COPPER.

Outputs structured, machine-parsable JSON logs with OpenTelemetry trace correlation,
agent/task contextual tags, and automatic credential/secret redaction.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from opentelemetry import trace

from app.core.logger import REDACTION_PATTERNS, RedactingFilter

LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "logs"


class JSONLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON with OpenTelemetry correlation."""

    def __init__(self, service_name: str = "copper"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        # Base structured payload
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }

        # Correlate with active OpenTelemetry span if available
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            log_payload["trace_id"] = f"{ctx.trace_id:032x}"
            log_payload["span_id"] = f"{ctx.span_id:016x}"

        # Extract extra contextual fields if present
        context_keys = [
            "session_id",
            "agent_id",
            "agent_type",
            "task_id",
            "model_name",
            "tool_name",
            "error_type",
            "security_event",
            "duration_ms",
        ]
        for key in context_keys:
            val = getattr(record, key, None)
            if val is not None:
                log_payload[key] = val

        # Include exception traceback if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        raw_json = json.dumps(log_payload, default=str)

        # Apply redaction filter over serialized JSON
        for pattern, repl in REDACTION_PATTERNS:
            raw_json = pattern.sub(repl, raw_json)

        return raw_json


def configure_structured_logging(
    log_dir: Path | None = None,
    enable_file_logging: bool = True,
    log_level: int = logging.INFO,
) -> logging.Logger:
    """Configures the root copper logger with both console and rotating JSON file sinks."""
    root_logger = logging.getLogger("copper")
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if re-initialized
    if any(isinstance(h.formatter, JSONLogFormatter) for h in root_logger.handlers):
        return root_logger

    # Ensure log directory exists
    target_dir = log_dir or LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / "copper.jsonl"

    if enable_file_logging:
        try:
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=15 * 1024 * 1024,  # 15 MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(JSONLogFormatter())
            file_handler.addFilter(RedactingFilter())
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Could not initialize rotating JSON file log: {e}")

    return root_logger


structured_logger = configure_structured_logging()


def get_json_logger(name: str = "copper", log_file: Optional[str] = None) -> logging.Logger:
    """Returns a logger instance configured with JSONLogFormatter and RedactingFilter."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if log_file:
        from logging.handlers import RotatingFileHandler

        handler = RotatingFileHandler(
            log_file,
            maxBytes=15 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(JSONLogFormatter())
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
    return logger
