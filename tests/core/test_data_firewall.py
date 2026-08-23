from app.core.data_firewall import (
    DataClass,
    FirewallResult,
    classify_and_redact,
    redact,
)


def test_firewall_public_text():
    result = classify_and_redact("This is a completely normal public message.")
    assert result.classification == DataClass.PUBLIC
    assert result.redaction_count == 0


def test_firewall_public_code_snippet():
    result = classify_and_redact("def add(a, b): return a + b")
    assert result.classification == DataClass.PUBLIC
    assert result.redaction_count == 0


def test_firewall_secret_openai_sk_legacy():
    result = classify_and_redact("My key is sk-1234567890abcdef1234567890abcdef")
    assert result.classification == DataClass.SECRET
    assert result.redaction_count >= 1
    assert "sk-•••REDACTED•••" in result.redacted_text


def test_firewall_secret_openai_sk_proj():
    result = classify_and_redact(
        "Secret: sk-proj-abcdef1234567890abcdef1234567890abcdef12"
    )
    assert result.classification == DataClass.SECRET
    assert "sk-•••REDACTED•••" in result.redacted_text


def test_firewall_secret_api_key_header():
    result = classify_and_redact("api_key: secret_super_secure_token_999")
    assert result.classification == DataClass.SECRET
    assert "•••CREDENTIAL_REDACTED•••" in result.redacted_text


def test_firewall_secret_bearer_token():
    result = classify_and_redact(
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    )
    assert result.classification == DataClass.SECRET
    assert "Authorization: Bearer •••REDACTED•••" in result.redacted_text


def test_firewall_sensitive_email_standard():
    result = classify_and_redact("Reach me at test@example.com")
    assert result.classification in [DataClass.SENSITIVE, DataClass.SECRET]
    assert "•••EMAIL_REDACTED•••" in result.redacted_text


def test_firewall_sensitive_email_subdomain():
    result = classify_and_redact("Send reports to admin.lead_ops@sub.corp.internal.io")
    assert "•••EMAIL_REDACTED•••" in result.redacted_text


def test_firewall_sensitive_phone_us():
    result = classify_and_redact("Call (555) 123-4567 today")
    assert result.classification in [DataClass.SENSITIVE, DataClass.SECRET]
    assert "•••PHONE_REDACTED•••" in result.redacted_text


def test_firewall_sensitive_phone_international():
    result = classify_and_redact("Mobile: +1-800-555-0199")
    assert "•••PHONE_REDACTED•••" in result.redacted_text


def test_firewall_sensitive_ipv4():
    result = classify_and_redact("Server IP is 192.168.1.254")
    assert result.classification in [DataClass.SENSITIVE, DataClass.SECRET]
    assert "•••IP_REDACTED•••" in result.redacted_text


def test_firewall_personal_home_path():
    result = classify_and_redact(
        "The file is located at /home/akash/documents/secret.txt"
    )
    assert result.classification in [
        DataClass.PERSONAL,
        DataClass.SENSITIVE,
        DataClass.SECRET,
    ]
    assert "•••PATH_REDACTED•••" in result.redacted_text


def test_firewall_personal_windows_path():
    result = classify_and_redact(r"Saved to C:\Users\Akash\secrets.env")
    assert result.classification in [
        DataClass.PERSONAL,
        DataClass.SENSITIVE,
        DataClass.SECRET,
    ]
    assert "•••PATH_REDACTED•••" in result.redacted_text


def test_firewall_sensitive_ssn():
    result = classify_and_redact("SSN: 123-45-6789")
    assert result.classification in [DataClass.SENSITIVE, DataClass.SECRET]
    assert "•••SSN_REDACTED•••" in result.redacted_text


def test_firewall_sensitive_credit_card():
    result = classify_and_redact("Credit card 4532 0150 1234 5678")
    assert result.classification in [DataClass.SENSITIVE, DataClass.SECRET]
    assert "•••CREDIT_CARD_REDACTED•••" in result.redacted_text


def test_firewall_multiple_patterns():
    text = (
        "User bob@corp.com with key sk-1234567890abcdef1234567890 and SSN 999-00-1111"
    )
    result = classify_and_redact(text)
    assert result.classification == DataClass.SECRET
    assert result.redaction_count >= 3
    assert "•••EMAIL_REDACTED•••" in result.redacted_text
    assert "sk-•••REDACTED•••" in result.redacted_text
    assert "•••SSN_REDACTED•••" in result.redacted_text


def test_firewall_convenience_redact():
    masked = redact("Email user@test.com")
    assert masked == "Email •••EMAIL_REDACTED•••"


def test_firewall_result_dataclass():
    res = FirewallResult(
        redacted_text="clean", classification=DataClass.PUBLIC, redaction_count=0
    )
    assert res.redacted_text == "clean"
    assert res.classification == DataClass.PUBLIC
    assert res.redaction_count == 0
