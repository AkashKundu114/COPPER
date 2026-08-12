import pytest
from app.core.data_firewall import classify_and_redact, DataClass

def test_public_text():
    result = classify_and_redact("This is a completely normal message.")
    assert result.classification == DataClass.PUBLIC
    assert result.redaction_count == 0
    assert result.redacted_text == "This is a completely normal message."

def test_secret_api_key():
    result = classify_and_redact("My openai key is sk-1234567890abcdef1234567890abcdef")
    assert result.classification == DataClass.SECRET
    assert result.redaction_count == 1
    assert "sk-•••REDACTED•••" in result.redacted_text

def test_sensitive_email():
    result = classify_and_redact("Contact me at test@example.com")
    assert result.classification == DataClass.SENSITIVE
    assert result.redaction_count == 1
    assert "•••EMAIL_REDACTED•••" in result.redacted_text

def test_sensitive_ssn():
    result = classify_and_redact("My SSN is 123-45-6789")
    assert result.classification == DataClass.SENSITIVE
    assert "•••SSN_REDACTED•••" in result.redacted_text

def test_sensitive_credit_card():
    result = classify_and_redact("Card: 1234-5678-9012-3456")
    assert result.classification == DataClass.SENSITIVE
    assert "•••CREDIT_CARD_REDACTED•••" in result.redacted_text

def test_multiple_patterns():
    result = classify_and_redact("Email test@example.com and key sk-1234567890abcdef12345")
    assert result.classification == DataClass.SECRET  # Secret is highest
    assert result.redaction_count == 2
    assert "•••EMAIL_REDACTED•••" in result.redacted_text
    assert "sk-•••REDACTED•••" in result.redacted_text
