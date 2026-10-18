"""Test fixtures.

Why fakeredis instead of a real Redis?
  - Tests must run anywhere (CI, a laptop, this VM) with zero infrastructure.
  - fakeredis implements the Redis commands we use (INCR, HSET, HGETALL,
    HINCRBY, EXPIRE) faithfully in memory.

How the override works: the app modules did `from app.redis_client import
get_redis`, so each holds its OWN reference to the function. Patching
app.redis_client.get_redis would NOT affect them — we must patch the
reference inside app.routers.links and app.rate_limit directly. This is a
classic Python gotcha worth remembering.
"""

import fakeredis
import pytest
from fastapi.testclient import TestClient

import app.rate_limit as rate_limit_mod
import app.routers.links as links_mod
from app.config import settings
from app.main import app


@pytest.fixture()
def redis_client(monkeypatch):
    """Fresh in-memory Redis for every test, wired into the app."""
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(links_mod, "get_redis", lambda: fake)
    monkeypatch.setattr(rate_limit_mod, "get_redis", lambda: fake)
    return fake


@pytest.fixture()
def client(redis_client):
    return TestClient(app)


@pytest.fixture()
def no_rate_limit(monkeypatch):
    """Raise the quota so bulk tests never trip the limiter."""
    monkeypatch.setattr(settings, "rate_limit_max_requests", 10_000)
