import pytest
from app.utils.validators import validate_message

def test_validate_message_valid():
    valid, err = validate_message('Hello, world!')
    assert valid is True
    assert err == ''

def test_validate_message_empty():
    valid, err = validate_message('   ')
    assert valid is False
    assert 'empty' in err

def test_validate_message_too_long():
    long_message = 'a' * 20001
    valid, err = validate_message(long_message)
    assert valid is False
    assert 'exceeds' in err