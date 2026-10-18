import fakeredis
import pytest
from fastapi.testclient import TestClient

import app.rate_limit as rate_limit_mod
import app.routers.links as links_mod
from app.config import settings
from app.main import app

@pytest.fixture()
def redis_client(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(links_mod, "get_redis", lambda: fake)
    monkeypatch.setattr(rate_limit_mod, "get_redis", lambda: fake)
    return fake

@pytest.fixture()
def client(redis_client):
    return TestClient(app)

@pytest.fixture()
def no_rate_limit(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_max_requests", 10_000)
