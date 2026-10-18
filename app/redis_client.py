"""Redis client wiring.

Why a module-level lazy client instead of creating one per request?
  - redis-py's client holds a connection *pool*; creating one per request
    would open/close TCP connections constantly and add latency.
  - One shared client is thread-safe and designed to be reused.

Why decode_responses=True?
  - Without it, every value comes back as bytes (b"https://...") and we'd
    sprinkle .decode() everywhere. Decoding once at the boundary is cleaner.
"""

from functools import lru_cache

import redis

from app.config import settings


@lru_cache
def get_redis() -> redis.Redis:
    """Return the shared Redis client (created once, reused forever)."""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
