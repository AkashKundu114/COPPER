import json
import logging
import os
import tempfile
import pytest

from app.core.json_logger import JSONLogFormatter, RedactingFilter, get_json_logger
from app.core.telemetry import init_telemetry, start_request_trace


@pytest.fixture(scope="module", autouse=True)
def setup_otel():
    init_telemetry()


def test_json_log_formatter_basic():
    """Verify JSONLogFormatter emits parseable JSON with core standard fields."""
    formatter = JSONLogFormatter(service_name="copper-test")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message execution",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["service"] == "copper-test"
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message execution"
    assert parsed["logger"] == "test_logger"
    assert "timestamp" in parsed


def test_json_log_formatter_context_fields():
    """Verify context-specific fields are preserved in formatted JSON output."""
    formatter = JSONLogFormatter(service_name="copper-test")
    record = logging.LogRecord(
        name="test_agent",
        level=logging.WARNING,
        pathname=__file__,
        lineno=25,
        msg="Agent execution warning",
        args=(),
        exc_info=None,
    )
    record.session_id = "sess-abc"
    record.agent_id = "agent-xyz"
    record.agent_type = "planner"
    record.task_id = "task-100"
    record.model_name = "qwen2.5-coder:14b"
    record.tool_name = "web_search"
    record.security_event = "rate_limit_exceeded"
    record.duration_ms = 145.2

    parsed = json.loads(formatter.format(record))
    assert parsed["session_id"] == "sess-abc"
    assert parsed["agent_id"] == "agent-xyz"
    assert parsed["agent_type"] == "planner"
    assert parsed["task_id"] == "task-100"
    assert parsed["model_name"] == "qwen2.5-coder:14b"
    assert parsed["tool_name"] == "web_search"
    assert parsed["security_event"] == "rate_limit_exceeded"
    assert parsed["duration_ms"] == 145.2


def test_json_log_formatter_otel_trace_correlation():
    """Verify trace_id and span_id are automatically extracted when inside an active OpenTelemetry span."""
    formatter = JSONLogFormatter(service_name="copper-test")

    span, trace_id, span_id = start_request_trace("test_logging_op", session_id="test_sess")
    try:
        record = logging.LogRecord(
            name="test_otel_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=45,
            msg="Trace correlated log",
            args=(),
            exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        assert "trace_id" in parsed
        assert "span_id" in parsed
        assert len(parsed["trace_id"]) == 32
        assert len(parsed["span_id"]) == 16
        assert parsed["trace_id"] == trace_id
    finally:
        span.end()


def test_redacting_filter_masks_secrets():
    """Verify RedactingFilter redacts bearer tokens, api keys, and passwords from logs."""
    redacting_filter = RedactingFilter()
    record = logging.LogRecord(
        name="test_secret",
        level=logging.INFO,
        pathname=__file__,
        lineno=60,
        msg="User authenticated with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 and token sk-proj-1234567890abcdef and password=SecretPassword123!",
        args=(),
        exc_info=None,
    )
    redacting_filter.filter(record)
    assert "Bearer [REDACTED_TOKEN]" in record.msg
    assert "[REDACTED_API_KEY]" in record.msg
    assert "password=[REDACTED]" in record.msg
    assert "SecretPassword123!" not in record.msg


def test_get_json_logger_creates_file_sink():
    """Verify get_json_logger writes JSON log line into disk log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logfile = os.path.join(tmpdir, "copper_test.jsonl")
        logger = get_json_logger("copper.test_module", log_file=logfile)
        logger.info("Structured event test message", extra={"session_id": "test-file-sess"})

        for h in logger.handlers:
            h.flush()

        assert os.path.exists(logfile)
        with open(logfile, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) >= 1
        data = json.loads(lines[-1])
        assert data["message"] == "Structured event test message"
        assert data["session_id"] == "test-file-sess"

        # Explicitly close and remove handlers to release file lock on Windows
        for h in list(logger.handlers):
            h.close()
            logger.removeHandler(h)
