"""Request/response schemas.

Why schemas separate from storage?
  - The API contract (what clients send/receive) and the storage layout
    (how Redis holds it) change for different reasons. Keeping them apart
    means we can rework Redis keys without breaking API clients.
"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    # HttpUrl rejects garbage like "not a url" with a clear 422 before our
    # code ever runs — validation at the boundary, not in business logic.
    url: HttpUrl

    # Optional vanity code, e.g. alias="promo" -> /promo.
    # Charset is restricted: an alias containing "/" would break routing
    # (FastAPI would parse it as extra path segments), and characters like
    # "?" or "#" would corrupt the URL. Letters, digits, "-" and "_" only.
    alias: str | None = Field(
        default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$"
    )

    # Optional lifetime in seconds. None = never expires.
    expires_in_seconds: int | None = Field(default=None, gt=0)


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    original_url: str
    expires_at: datetime | None = None


class StatsResponse(BaseModel):
    code: str
    original_url: str
    clicks: int
    created_at: datetime
    expires_at: datetime | None = None
