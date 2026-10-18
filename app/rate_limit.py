"""Per-IP rate limiting for the shorten endpoint.

Strategy: fixed window counter in Redis.
  - Key: ratelimit:{ip}:{window_start} -> INCR on each request, EXPIRE = window.
  - If the counter exceeds the max, reject with 429.

Why fixed window instead of sliding window?
  - Fixed window needs exactly 2 Redis commands (INCR + EXPIRE) and one key.
  - Sliding window (sorted set of timestamps, ZREMRANGEBYSCORE...) is more
    precise but heavier. For abuse protection on a small API, fixed window
    is the standard pragmatic choice.
  - Known edge: a burst at the very end of one window + start of the next
    can briefly double the effective rate. Acceptable here; documented.

Why limit by IP and not by user? This API has no auth — IP is the only
client identity available. Behind proxies you'd use X-Forwarded-For;
out of scope here, noted in the README.
"""

from fastapi import HTTPException, Request, status

from app.config import settings
from app.redis_client import get_redis


def check_rate_limit(request: Request) -> None:
    """Raise 429 if this IP exceeded its shorten quota for the current window."""
    # FastAPI's TestClient reports host "testclient" — fine, it still keys
    # consistently per test.
    ip = request.client.host if request.client else "unknown"
    window = settings.rate_limit_window_seconds
    max_requests = settings.rate_limit_max_requests

    r = get_redis()
    # Integer-divide the epoch by the window so all requests in the same
    # window share one key, e.g. ratelimit:1.2.3.4:29240123
    import time

    window_id = int(time.time()) // window
    key = f"ratelimit:{ip}:{window_id}"

    count = r.incr(key)
    if count == 1:
        # First hit in this window: arm the key's self-destruct so stale
        # windows don't pile up in Redis forever.
        r.expire(key, window)

    if count > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {max_requests} requests per {window}s",
        )
