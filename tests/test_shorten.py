"""Tests for POST /shorten."""

import pytest


def test_shorten_returns_code_and_url(client, no_rate_limit):
    resp = client.post("/shorten", json={"url": "https://example.com/article"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"]  # auto-generated base62 code
    assert body["short_url"].endswith(f"/{body['code']}")
    assert body["original_url"] == "https://example.com/article"
    assert body["expires_at"] is None


def test_shorten_codes_are_unique(client, no_rate_limit):
    codes = {
        client.post("/shorten", json={"url": f"https://example.com/{i}"}).json()["code"]
        for i in range(20)
    }
    # The atomic counter guarantees this; the test pins the behavior.
    assert len(codes) == 20


def test_custom_alias(client, no_rate_limit):
    resp = client.post(
        "/shorten", json={"url": "https://example.com", "alias": "mypromo"}
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "mypromo"


def test_alias_collision_returns_409(client, no_rate_limit):
    client.post("/shorten", json={"url": "https://example.com/a", "alias": "taken"})
    resp = client.post(
        "/shorten", json={"url": "https://example.com/b", "alias": "taken"}
    )
    assert resp.status_code == 409


def test_invalid_url_rejected(client, no_rate_limit):
    resp = client.post("/shorten", json={"url": "not a url"})
    assert resp.status_code == 422


def test_self_reference_rejected(client, no_rate_limit, monkeypatch):
    """Shortening our own short URL would create a redirect loop."""
    from app.config import settings

    monkeypatch.setattr(settings, "base_url", "http://localhost:8000")
    resp = client.post("/shorten", json={"url": "http://localhost:8000/abc123"})
    assert resp.status_code == 422


def test_expiry_is_stored(client, no_rate_limit):
    resp = client.post(
        "/shorten",
        json={"url": "https://example.com", "expires_in_seconds": 3600},
    )
    assert resp.status_code == 201
    assert resp.json()["expires_at"] is not None
