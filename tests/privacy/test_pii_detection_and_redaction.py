import pytest

from app.core.data_firewall import (
    DataClass,
    classify_and_redact,
    redact,
)


def test_pii_sanitization_patterns():
    """Verify DataFirewall accurately classifies and redacts credentials, PII, and paths."""
    # 1. Private Key -> RESTRICTED/SECRET
    pk = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----"
    r_pk = classify_and_redact(pk)
    assert r_pk.classification in (DataClass.RESTRICTED, DataClass.SECRET)
    assert "•••PRIVATE_KEY_REDACTED•••" in r_pk.redacted_text

    # 2. API Key -> RESTRICTED/SECRET
    api_key_text = "Here is my key: sk-ant-api03-abcdef1234567890abcdef1234567890"
    r_ak = classify_and_redact(api_key_text)
    assert r_ak.classification in (DataClass.RESTRICTED, DataClass.SECRET)
    assert "sk-ant-•••REDACTED•••" in r_ak.redacted_text

    # 3. Email -> SENSITIVE
    email_text = "Contact me at alice.smith@protonmail.com for the secret"
    r_em = classify_and_redact(email_text)
    assert r_em.classification == DataClass.SENSITIVE
    assert "•••EMAIL_REDACTED•••" in r_em.redacted_text

    # 4. Social Security Number -> SENSITIVE
    ssn_text = "SSN: 123-45-6789"
    r_ssn = classify_and_redact(ssn_text)
    assert r_ssn.classification == DataClass.SENSITIVE
    assert "•••SSN_REDACTED•••" in r_ssn.redacted_text

    # 5. Local Path -> PERSONAL
    path_text = "Log saved in C:\\Users\\Administrator\\Desktop\\report.txt"
    r_path = classify_and_redact(path_text)
    assert r_path.classification == DataClass.PERSONAL
    assert "•••PATH_REDACTED•••" in r_path.redacted_text


def test_public_text_clean():
    """Verify harmless public text is classified as PUBLIC with zero redactions."""
    public_text = "Python is an interpreted, high-level, general-purpose programming language."
    r = classify_and_redact(public_text)
    assert r.classification == DataClass.PUBLIC
    assert r.redaction_count == 0
    assert r.redacted_text == public_text
    assert r.audit_hash == ""
