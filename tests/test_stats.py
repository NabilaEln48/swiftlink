"""Tests for GET /{code}/stats."""


def test_stats_reflects_link_data(client, no_rate_limit):
    code = client.post(
        "/shorten", json={"url": "https://example.com/x"}
    ).json()["code"]
    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)

    resp = client.get(f"/{code}/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == code
    assert body["original_url"] == "https://example.com/x"
    assert body["clicks"] == 2
    assert body["created_at"]  # ISO timestamp present


def test_stats_unknown_code_404(client, no_rate_limit):
    assert client.get("/ghost/stats").status_code == 404
