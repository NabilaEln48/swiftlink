from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

class ShortenRequest(BaseModel):

    url: HttpUrl

    alias: str | None = Field(
        default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$"
    )

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
