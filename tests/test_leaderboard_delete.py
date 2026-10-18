"""Tests for alias charset validation, DELETE, and the leaderboard."""


def test_alias_with_slash_rejected(client, no_rate_limit):
    resp = client.post(
        "/shorten", json={"url": "https://example.com", "alias": "a/b"}
    )
    assert resp.status_code == 422


def test_alias_with_special_chars_rejected(client, no_rate_limit):
    resp = client.post(
        "/shorten", json={"url": "https://example.com", "alias": "sale?!2026"}
    )
    assert resp.status_code == 422


def test_alias_with_dashes_and_underscores_ok(client, no_rate_limit):
    resp = client.post(
        "/shorten", json={"url": "https://example.com", "alias": "my_sale-2026"}
    )
    assert resp.status_code == 201


def test_delete_link(client, no_rate_limit):
    code = client.post(
        "/shorten", json={"url": "https://example.com", "alias": "todelete"}
    ).json()["code"]
    resp = client.delete(f"/{code}")
    assert resp.status_code == 204
    # Gone for good: redirect now 404s.
    assert client.get(f"/{code}", follow_redirects=False).status_code == 404


def test_delete_missing_code_404(client, no_rate_limit):
    assert client.delete("/never-existed").status_code == 404


def test_leaderboard_ranks_by_clicks(client, no_rate_limit):
    codes = [
        client.post("/shorten", json={"url": f"https://example.com/{i}"}).json()["code"]
        for i in range(3)
    ]
    for _ in range(5):
        client.get(f"/{codes[1]}", follow_redirects=False)
    for _ in range(2):
        client.get(f"/{codes[0]}", follow_redirects=False)

    top = client.get("/leaderboard").json()["top"]
    assert top[0] == {"code": codes[1], "clicks": 5}
    assert top[1] == {"code": codes[0], "clicks": 2}


def test_leaderboard_ignores_deleted_links(client, no_rate_limit):
    code = client.post(
        "/shorten", json={"url": "https://example.com", "alias": "goner"}
    ).json()["code"]
    client.get(f"/{code}", follow_redirects=False)
    client.delete(f"/{code}")
    codes = [entry["code"] for entry in client.get("/leaderboard").json()["top"]]
    assert code not in codes
