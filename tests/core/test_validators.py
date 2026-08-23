from app.utils.validators import validate_message


def test_validate_message_clean_english():
    valid, err = validate_message("Hello, world!")
    assert valid is True
    assert err == ""


def test_validate_message_code_snippet():
    valid, err = validate_message("def foo(): return 42")
    assert valid is True
    assert err == ""


def test_validate_message_unicode():
    valid, err = validate_message(
        "🌟 Testing multi-byte utf-8 unicode characters: こんにちは"
    )
    assert valid is True
    assert err == ""


def test_validate_message_whitespace_only():
    valid, err = validate_message("   \t\n  ")
    assert valid is False
    assert "empty" in err.lower()


def test_validate_message_empty_string():
    valid, err = validate_message("")
    assert valid is False
    assert "empty" in err.lower()


def test_validate_message_max_length_bound():
    message_20k = "a" * 20000
    valid, _err = validate_message(message_20k)
    assert valid is True


def test_validate_message_exceeds_max_length():
    message_over = "a" * 20001
    valid, err = validate_message(message_over)
    assert valid is False
    assert "exceeds" in err.lower()
