"""Expiry and rate-limit tests."""

import time


def test_expired_link_returns_410(client, no_rate_limit):
    code = client.post(
        "/shorten",
        json={"url": "https://example.com", "expires_in_seconds": 1},
    ).json()["code"]
    time.sleep(1.2)  # let the TTL lapse; 1.2s keeps the suite fast
    resp = client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 410


def test_rate_limit_blocks_after_quota(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rate_limit_max_requests", 2)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)

    assert client.post("/shorten", json={"url": "https://a.com"}).status_code == 201
    assert client.post("/shorten", json={"url": "https://b.com"}).status_code == 201
    # Third request inside the same window -> 429.
    resp = client.post("/shorten", json={"url": "https://c.com"})
    assert resp.status_code == 429
