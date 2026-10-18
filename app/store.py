from datetime import datetime, timezone

import redis

COUNTER_KEY = "swiftlink:counter"

def _key(code: str) -> str:
    return f"link:{code}"

def next_code_number(r: redis.Redis) -> int:
    return int(r.incr(COUNTER_KEY))

def create_link(
    r: redis.Redis,
    code: str,
    url: str,
    expires_at: datetime | None,
) -> bool:
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
    data = r.hgetall(_key(code))
    return data or None

def record_click(r: redis.Redis, code: str) -> int:
    return int(r.hincrby(_key(code), "clicks", 1))

def is_expired(link: dict) -> bool:
    expires_at = link.get("expires_at")
    if not expires_at:
        return False
    return datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc)

LEADERBOARD_KEY = "swiftlink:leaderboard"

def record_leaderboard_hit(r: redis.Redis, code: str) -> None:
    r.zincrby(LEADERBOARD_KEY, 1, code)

def top_links(r: redis.Redis, limit: int = 10) -> list[tuple[str, int]]:
    return [
        (code, int(score))
        for code, score in r.zrevrange(LEADERBOARD_KEY, 0, limit - 1, withscores=True)
    ]

def delete_link(r: redis.Redis, code: str) -> bool:
    key = _key(code)
    if not r.exists(key):
        return False
    pipe = r.pipeline()
    pipe.delete(key)
    pipe.zrem(LEADERBOARD_KEY, code)
    pipe.execute()
    return True
