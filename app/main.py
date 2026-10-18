from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import links

app = FastAPI(
    title="swiftlink",
    description="URL shortener API — FastAPI + Redis",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(links.router)
