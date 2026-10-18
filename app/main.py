"""Application entrypoint.

Run locally with:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import links

app = FastAPI(
    title="swiftlink",
    description="URL shortener API — FastAPI + Redis",
    version="0.1.0",
)

# Permissive CORS for development: a future frontend (different origin)
# needs to call this API from the browser. Tighten allow_origins in
# production — "*" means any website can make requests on users' behalf.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# /health is registered BEFORE the links router so the catch-all /{code}
# route can never shadow it (defense in depth; /{code} only matches one
# segment anyway, but explicit ordering removes all doubt).
@app.get("/health")
def health():
    """Liveness probe for load balancers / container orchestration."""
    return {"status": "ok"}


app.include_router(links.router)
