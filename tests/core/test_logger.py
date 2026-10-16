import logging

from app.core.logger import get_logger, logger


def test_get_logger_default():
    log_instance = get_logger("test_copper")
    assert isinstance(log_instance, logging.Logger)
    assert log_instance.level == logging.INFO


def test_logger_singleton():
    assert isinstance(logger, logging.Logger)
    assert logger.name == "copper"


def test_logger_has_handlers():
    assert len(logger.handlers) >= 1


def test_logger_formatter():
    handler = logger.handlers[0]
    assert handler.formatter is not None


def test_logger_info_call():
    logger.info("Unit test log info line")


def test_logger_warning_call():
    logger.warning("Unit test log warning line")


def test_logger_error_call():
    logger.error("Unit test log error line")


def test_logger_idempotent_get():
    l1 = get_logger("idempotent_test")
    l2 = get_logger("idempotent_test")
    assert l1 is l2


def test_logger_redaction_secrets():
    from app.core.logger import RedactingFilter

    rf = RedactingFilter()

    # 1. OpenAI / Anthropic API Key
    rec1 = logging.LogRecord("test", logging.INFO, "test.py", 10, "Connecting with sk-proj-1234567890abcdef1234567890", (), None)
    rf.filter(rec1)
    assert "sk-proj-" not in rec1.msg
    assert "[REDACTED_API_KEY]" in rec1.msg

    # 2. Bearer token
    rec2 = logging.LogRecord("test", logging.INFO, "test.py", 11, "Auth: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc", (), None)
    rf.filter(rec2)
    assert "eyJhbGci" not in rec2.msg
    assert "Bearer [REDACTED_TOKEN]" in rec2.msg

    # 3. Password field
    rec3 = logging.LogRecord("test", logging.INFO, "test.py", 12, "User login with password=SuperSecretPassword123!", (), None)
    rf.filter(rec3)
    assert "SuperSecretPassword123!" not in rec3.msg
    assert "password=[REDACTED]" in rec3.msg
