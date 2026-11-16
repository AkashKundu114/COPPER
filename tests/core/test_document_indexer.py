import pytest

from app.core.document_indexer import chunk_text


def test_chunk_text_returns_empty_for_none_or_empty_text():
    assert chunk_text(None) == []
    assert chunk_text("") == []


@pytest.mark.parametrize("value", [123, b"bytes", ["not", "text"], ["a", "b"]])
def test_chunk_text_rejects_non_string_text(value):
    with pytest.raises(TypeError, match="text must be a string"):
        chunk_text(value)


@pytest.mark.parametrize("chunk_size", [1.5, "100", True])
def test_chunk_text_rejects_non_integer_chunk_size(chunk_size):
    with pytest.raises(TypeError, match="chunk_size must be an integer"):
        chunk_text("", chunk_size=chunk_size)


@pytest.mark.parametrize("overlap", [2.5, "10", False])
def test_chunk_text_rejects_non_integer_overlap(overlap):
    with pytest.raises(TypeError, match="overlap must be an integer"):
        chunk_text(None, overlap=overlap)


def test_chunk_text_keeps_existing_overlap_clamping():
    chunks = chunk_text("abcdefghijklmnopqrstuvwxyz", chunk_size=10, overlap=20)
    assert chunks == ["abcdefghij", "jklmnopqrs", "stuvwxyz"]
