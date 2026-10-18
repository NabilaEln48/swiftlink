from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app import store
from app.config import settings
from app.rate_limit import check_rate_limit
from app.redis_client import get_redis
from app.schemas import ShortenRequest, ShortenResponse, StatsResponse
from app.shortener import encode_base62

router = APIRouter()

def _reject_self_reference(url: str) -> None:
    target_host = urlparse(str(url)).hostname
    own_host = urlparse(settings.base_url).hostname
    if target_host and own_host and target_host.lower() == own_host.lower():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Cannot shorten a URL pointing to this service (redirect loop)",
        )

@router.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_rate_limit)],
)
def shorten_link(payload: ShortenRequest):
    _reject_self_reference(str(payload.url))
    r = get_redis()

    if payload.alias:

        code = payload.alias
        taken = not store.create_link(
            r, code, str(payload.url), _expires_at(payload.expires_in_seconds)
        )
        if taken:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Alias '{code}' is already taken",
            )
    else:

        code = encode_base62(store.next_code_number(r))
        store.create_link(
            r, code, str(payload.url), _expires_at(payload.expires_in_seconds)
        )

    link = store.get_link(r, code)
    assert link is not None
    return ShortenResponse(
        code=code,
        short_url=f"{settings.base_url.rstrip('/')}/{code}",
        original_url=str(payload.url),
        expires_at=_parse_dt(link["expires_at"]),
    )

def _expires_at(seconds: int | None) -> datetime | None:
    if seconds is None:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)

def _parse_dt(value: str) -> datetime | None:
    return datetime.fromisoformat(value) if value else None

@router.get("/{code}/stats", response_model=StatsResponse)
def link_stats(code: str):
    link = store.get_link(get_redis(), code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    return StatsResponse(
        code=code,
        original_url=link["url"],
        clicks=int(link["clicks"]),
        created_at=datetime.fromisoformat(link["created_at"]),
        expires_at=_parse_dt(link["expires_at"]),
    )

@router.get("/leaderboard")
def leaderboard(limit: int = 10):
    entries = store.top_links(get_redis(), limit=max(1, min(limit, 100)))
    return {"top": [{"code": code, "clicks": clicks} for code, clicks in entries]}

@router.get("/{code}")
def redirect_link(code: str):
    r = get_redis()
    link = store.get_link(r, code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    if store.is_expired(link):

        raise HTTPException(status_code=410, detail="Short link has expired")
    store.record_click(r, code)
    store.record_leaderboard_hit(r, code)
    return RedirectResponse(url=link["url"], status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(code: str):
    if not store.delete_link(get_redis(), code):
        raise HTTPException(status_code=404, detail="Short link not found")
    return None
