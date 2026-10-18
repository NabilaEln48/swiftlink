def _shorten(client, url="https://example.com/page", **kwargs):
    resp = client.post("/shorten", json={"url": url, **kwargs})
    assert resp.status_code == 201
    return resp.json()["code"]

def test_redirect_returns_307_with_location(client, no_rate_limit):
    code = _shorten(client)

    resp = client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com/page"

def test_redirect_counts_clicks(client, no_rate_limit):
    code = _shorten(client)
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)
    stats = client.get(f"/{code}/stats").json()
    assert stats["clicks"] == 3

def test_unknown_code_returns_404(client, no_rate_limit):
    resp = client.get("/nope-not-real", follow_redirects=False)
    assert resp.status_code == 404
