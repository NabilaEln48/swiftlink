"""Application entrypoint.

Run locally with:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.routers import links

app = FastAPI(
    title="swiftlink",
    description="URL shortener API — FastAPI + Redis",
    version="0.1.0",
)

# /health is registered BEFORE the links router so the catch-all /{code}
# route can never shadow it (defense in depth; /{code} only matches one
# segment anyway, but explicit ordering removes all doubt).
@app.get("/health")
def health():
    """Liveness probe for load balancers / container orchestration."""
    return {"status": "ok"}


app.include_router(links.router)
