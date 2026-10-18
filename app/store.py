"""Redis storage layout.

Keys:
  link:{code}          -> hash {url, created_at, clicks, expires_at}
  swiftlink:counter    -> integer, bumped by INCR to mint the next code

Why a hash per link instead of separate keys?
  - One round trip fetches everything the redirect needs (url + expiry).
  - HINCRBY gives us an *atomic* click counter inside the same hash —
    no separate key to keep in sync.

Why no Redis key TTL for expiry?
  - If Redis evicted expired keys, we couldn't tell "expired" apart from
    "never existed" — and we want 410 Gone for the former, 404 for the
    latter. So expiry is checked in application code against expires_at.
  - Trade-off: dead keys accumulate. A production service would run a
    periodic sweeper; that's out of scope here and noted in the README.
"""

from datetime import datetime, timezone

import redis

COUNTER_KEY = "swiftlink:counter"


def _key(code: str) -> str:
    return f"link:{code}"


def next_code_number(r: redis.Redis) -> int:
    """Atomically bump the global counter. INCR is single-threaded in Redis,
    so two concurrent requests can never receive the same number."""
    return int(r.incr(COUNTER_KEY))


def create_link(
    r: redis.Redis,
    code: str,
    url: str,
    expires_at: datetime | None,
) -> bool:
    """Store a new link. Returns False if the code is already taken
    (used for custom-alias collision detection)."""
    key = _key(code)
    if r.exists(key):
        return False
    now = datetime.now(timezone.utc).isoformat()
    r.hset(
        key,
        mapping={
            "url": url,
            "created_at": now,
            "clicks": 0,
            "expires_at": expires_at.isoformat() if expires_at else "",
        },
    )
    return True


def get_link(r: redis.Redis, code: str) -> dict | None:
    """Fetch a link's data, or None if the code doesn't exist."""
    data = r.hgetall(_key(code))
    return data or None


def record_click(r: redis.Redis, code: str) -> int:
    """Atomically increment the click counter and return the new total.

    Why atomic matters: with a naive read-modify-write (GET, +1, SET), two
    simultaneous redirects could both read 5 and both write 6 — losing a
    click. HINCRBY executes as one indivisible step inside Redis.
    """
    return int(r.hincrby(_key(code), "clicks", 1))


def is_expired(link: dict) -> bool:
    """True if the link has an expires_at in the past."""
    expires_at = link.get("expires_at")
    if not expires_at:
        return False
    return datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc)
