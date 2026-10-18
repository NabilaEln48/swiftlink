"""Link endpoints: shorten, redirect, stats.

Route ordering note: /{code}/stats is registered BEFORE /{code} so the
more specific path always wins, even though /{code} only matches a single
segment and couldn't actually swallow it. Explicit > clever.
"""

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
    """Refuse to shorten links pointing back at this service.

    Why: shortening our own short URL would create a redirect loop
    (GET /abc -> 307 to /abc -> ...). Browsers detect loops, but the
    click counter would inflate and it's never what the user wanted.
    """
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
    """Create a short link. Rate-limited per IP (see app/rate_limit.py)."""
    _reject_self_reference(str(payload.url))
    r = get_redis()

    if payload.alias:
        # Custom alias: user picks the code. Collision -> 409, not silent
        # overwrite — silently stealing someone's alias would be a bug.
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
        # Auto code: atomic counter -> base62. Uniqueness is guaranteed by
        # the counter, so no collision check is needed here.
        code = encode_base62(store.next_code_number(r))
        store.create_link(
            r, code, str(payload.url), _expires_at(payload.expires_in_seconds)
        )

    link = store.get_link(r, code)
    assert link is not None  # we just created it
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
    """Click analytics for a short link."""
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
    """Top short links by clicks. Registered BEFORE /{code}: otherwise the
    literal path "leaderboard" would be captured as a code and 404."""
    entries = store.top_links(get_redis(), limit=max(1, min(limit, 100)))
    return {"top": [{"code": code, "clicks": clicks} for code, clicks in entries]}


@router.get("/{code}")
def redirect_link(code: str):
    """Resolve a short code to its target with an HTTP 307 redirect.

    Why 307 and not 302? 302 historically lets clients change POST -> GET
    on redirect; 307 guarantees the method and body are preserved. For a
    link shortener the practical difference is nil, but 307 is the
    semantically correct "temporary redirect".
    """
    r = get_redis()
    link = store.get_link(r, code)
    if link is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    if store.is_expired(link):
        # 410 Gone (not 404): the link *existed* but is no longer available.
        # The distinction helps clients and is good HTTP hygiene.
        raise HTTPException(status_code=410, detail="Short link has expired")
    store.record_click(r, code)
    store.record_leaderboard_hit(r, code)
    return RedirectResponse(url=link["url"], status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(code: str):
    """Retire a short link. Idempotent from the client's view: missing
    codes 404 rather than silently succeeding, so callers know the state."""
    if not store.delete_link(get_redis(), code):
        raise HTTPException(status_code=404, detail="Short link not found")
    return None
