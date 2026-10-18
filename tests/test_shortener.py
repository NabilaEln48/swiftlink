"""Unit tests for the base62 encoder (no app needed)."""

from app.shortener import encode_base62


def test_zero():
    assert encode_base62(0) == "0"


def test_known_values():
    assert encode_base62(61) == "Z"  # last single char
    assert encode_base62(62) == "10"  # rolls over like decimal 10
    assert encode_base62(3844) == "100"  # 62^2


def test_output_uses_url_safe_alphabet():
    alphabet = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    for n in (1, 100, 99999, 10**12):
        assert set(encode_base62(n)) <= alphabet


def test_negative_rejected():
    import pytest

    with pytest.raises(ValueError):
        encode_base62(-1)
