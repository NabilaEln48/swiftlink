# swiftlink

A URL shortener API built with **FastAPI** + **Redis**. Shortens URLs into base62 codes, tracks clicks, enforces per-IP rate limits, and supports custom aliases and link expiry.

## Quick start

```bash
# 1. Start Redis
docker compose up -d

# 2. Install & run
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # optional — defaults work for local dev
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API docs.

## API

| Method | Path             | Description                                        |
|--------|------------------|----------------------------------------------------|
| POST   | `/shorten`       | Create a short link (rate-limited: 10/min per IP)   |
| GET    | `/{code}`        | 307 redirect to the original URL, counts a click   |
| GET    | `/{code}/stats`  | Click analytics for a link                         |
| GET    | `/health`        | Liveness probe                                      |

**Create a link:**

```bash
curl -X POST localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/article"}'
# {"code":"1","short_url":"http://localhost:8000/1","original_url":"...","expires_at":null}
```

**With options:**

```bash
curl -X POST localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/sale", "alias": "sale", "expires_in_seconds": 86400}'
```

**Status codes:** `201` created · `307` redirect · `404` unknown code · `409` alias taken · `410` link expired · `422` invalid/self-referencing URL · `429` rate limited.

## Design decisions

- **Redis as the primary store.** A shortener's access pattern is "tiny value, keyed lookup, counters, TTLs" — exactly what Redis is for. One `HGETALL` fetches everything a redirect needs.
- **Counter → base62 codes.** An atomic `INCR` counter guarantees unique codes with zero collision retries; base62 keeps them short and URL-safe (unlike base64's `+/=`). Trade-off: codes are guessable — fine here, not for private links.
- **Atomic click counting.** `HINCRBY` is a single indivisible step; a naive read-modify-write would lose clicks under concurrency.
- **Fixed-window rate limiting.** 2 Redis commands per request vs. a heavier sliding-window log — the standard pragmatic choice for abuse protection.
- **410 vs 404.** Expired links return `410 Gone` (it existed, it's over) instead of `404` — correct HTTP semantics. Expiry is checked in app code rather than via Redis TTL so the distinction survives.
- **307 redirects** preserve the HTTP method; `302` historically doesn't.

## Configuration

All via environment (see `.env.example`): `REDIS_URL`, `BASE_URL`, `RATE_LIMIT_MAX_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`.

## Tests

```bash
pytest -q   # 18 tests, fakeredis — no real Redis needed
```

## Known simplifications

- No auth: rate limiting is per-IP, which is spoofable behind shared NAT.
- Dead (expired) keys accumulate — a production service would run a sweeper.
- Single Redis instance: no replication/sharding story for massive scale.
