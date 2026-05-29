# REQ-SHORT-001, REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004, REQ-SHORT-005, REQ-SHORT-006
# FastAPI application entry point — URL Shortener Service
# Spec: specs/url-shortener.yaml | SPEC-SHORT-001 v1.0.0

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .database import Base, engine, SessionLocal
from .models import ShortenedUrl, Blocklist
from .routers import urls
from .crud import seed_blocklist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# REQ-SHORT-005: seed blocklist domains loaded from environment variable
_DEFAULT_BLOCKED_DOMAINS = [
    "malware.example.com",
    "phishing.example.com",
    "bit.ly",          # prevent short-URL chaining
    "tinyurl.com",     # prevent short-URL chaining
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    # Seed the blocklist
    db = SessionLocal()
    try:
        env_blocked = os.getenv("BLOCKED_DOMAINS", "")
        extra = [d.strip() for d in env_blocked.split(",") if d.strip()]
        seed_blocklist(db, _DEFAULT_BLOCKED_DOMAINS + extra)
    finally:
        db.close()
    yield


app = FastAPI(
    title="URL Shortener Service",
    description=(
        "A RESTful URL shortening service with analytics, expiry support, "
        "and malicious URL detection. "
        "Spec: SPEC-SHORT-001 v1.0.0"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(urls.router)


@app.get("/api/health", tags=["health"], summary="Health check — REQ-SHORT-006")
def health_check():
    """
    REQ-SHORT-006: Returns HTTP 200 with service status.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"status_code": 404, "error": "NOT_FOUND", "detail": str(exc.detail)},
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "error": "INTERNAL_ERROR",
            "detail": "An unexpected error occurred",
        },
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )
