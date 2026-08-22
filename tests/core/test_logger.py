import logging
from app.core.logger import get_logger, logger


def test_get_logger_default():
    l = get_logger("test_copper")
    assert isinstance(l, logging.Logger)
    assert l.level == logging.INFO


def test_logger_singleton():
    assert isinstance(logger, logging.Logger)
    assert logger.name == "copper"


def test_logger_has_handlers():
    assert len(logger.handlers) >= 1


def test_logger_formatter():
    handler = logger.handlers[0]
    assert handler.formatter is not None


def test_logger_info_call():
    # Calling info should not throw
    logger.info("Unit test log info line")


def test_logger_warning_call():
    logger.warning("Unit test log warning line")


def test_logger_error_call():
    logger.error("Unit test log error line")


def test_logger_idempotent_get():
    l1 = get_logger("idempotent_test")
    l2 = get_logger("idempotent_test")
    assert l1 is l2
