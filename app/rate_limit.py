from fastapi import HTTPException, Request, status

from app.config import settings
from app.redis_client import get_redis

def check_rate_limit(request: Request) -> None:

    ip = request.client.host if request.client else "unknown"
    window = settings.rate_limit_window_seconds
    max_requests = settings.rate_limit_max_requests

    r = get_redis()

    import time

    window_id = int(time.time()) // window
    key = f"ratelimit:{ip}:{window_id}"

    count = r.incr(key)
    if count == 1:

        r.expire(key, window)

    if count > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {max_requests} requests per {window}s",
        )
