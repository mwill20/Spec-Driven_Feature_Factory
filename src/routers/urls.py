# REQ-SHORT-001, REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004, REQ-SHORT-005, REQ-SHORT-006
# URL creation and management endpoints.

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..crud import (
    create_short_url,
    delete_url,
    get_blocked_domains,
    get_url_by_code,
    record_redirect,
)
from ..database import get_db
from ..schemas import ErrorResponse, UrlCreateRequest, UrlCreateResponse, UrlInfoResponse
from ..utils import UrlValidationError, validate_url

logger = logging.getLogger(__name__)
router = APIRouter()

BASE_URL = "http://localhost:8000"


def _build_short_url(code: str) -> str:
    import os
    base = os.getenv("BASE_URL", BASE_URL).rstrip("/")
    return f"{base}/{code}"


@router.post(
    "/urls",
    response_model=UrlCreateResponse,
    status_code=201,
    summary="Shorten a URL",
    description="REQ-SHORT-001, REQ-SHORT-004, REQ-SHORT-005",
)
def shorten_url(
    body: UrlCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> UrlCreateResponse:
    """
    REQ-SHORT-001: Accept valid URL, return 6-char short code.
    REQ-SHORT-004: Support optional expiration date.
    REQ-SHORT-005: Validate URL; reject invalid, blocked, private-IP URLs.
    REQ-SHORT-006: Structured error responses on all failure paths.
    """
    blocked_domains = get_blocked_domains(db)

    try:
        validated_url = validate_url(body.url, blocked_domains=blocked_domains)
    except UrlValidationError as exc:
        logger.warning(
            "url_validation_failed ip=%s url=%.100s error=%s",
            request.client.host if request.client else "unknown",
            body.url,
            exc.error_code,
        )
        if exc.error_code == "BLOCKED":
            raise HTTPException(
                status_code=400,
                detail={"error": "BLOCKED", "detail": str(exc)},
            )
        raise HTTPException(
            status_code=422,
            detail={"error": exc.error_code, "detail": str(exc)},
        )

    record, already_exists = create_short_url(
        db, validated_url, expires_at=body.expires_at
    )

    logger.info(
        "url_created code=%s already_exists=%s ip=%s",
        record.short_code,
        already_exists,
        request.client.host if request.client else "unknown",
    )

    status_code = 200 if already_exists else 201
    response = UrlCreateResponse(
        short_code=record.short_code,
        short_url=_build_short_url(record.short_code),
        url=record.original_url,
        expires_at=record.expires_at,
        created_at=record.created_at,
        already_exists=already_exists,
    )

    from fastapi.responses import JSONResponse
    import json

    return JSONResponse(content=response.model_dump(mode="json"), status_code=status_code)


@router.get(
    "/{code}",
    summary="Redirect to original URL",
    description="REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004",
    responses={
        302: {"description": "Redirect to original URL"},
        404: {"description": "Short code not found"},
        410: {"description": "URL has expired"},
    },
)
def redirect_to_url(
    code: str,
    request: Request,
    referer: str = Header(None, alias="referer"),
    db: Session = Depends(get_db),
):
    """
    REQ-SHORT-002: GET /{code} → 302 redirect to original URL.
    REQ-SHORT-003: Increment click_count, update last_accessed, store referrer.
    REQ-SHORT-004: Return 410 if URL is expired.
    """
    record = get_url_by_code(db, code)

    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "detail": "Short code not found"},
        )

    # REQ-SHORT-004: check expiry at redirect time.
    # SQLite returns naive datetimes; normalize to UTC before comparing.
    if record.expires_at:
        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
    if record.expires_at and datetime.now(timezone.utc) > expires:
        raise HTTPException(
            status_code=410,
            detail={"error": "EXPIRED", "detail": "URL has expired"},
        )

    # REQ-SHORT-003: record analytics
    record_redirect(db, record, referrer=referer)

    logger.info(
        "redirect code=%s click_count=%d ip=%s",
        code,
        record.click_count,
        request.client.host if request.client else "unknown",
    )

    return RedirectResponse(url=record.original_url, status_code=302)


@router.get(
    "/api/urls/{code}",
    response_model=UrlInfoResponse,
    summary="Get URL info and analytics",
    description="REQ-SHORT-003, REQ-SHORT-006",
)
def get_url_info(code: str, db: Session = Depends(get_db)) -> UrlInfoResponse:
    """
    REQ-SHORT-003: Return full analytics (click_count, last_accessed, referrer).
    REQ-SHORT-006: Structured response with all metadata.
    """
    record = get_url_by_code(db, code)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "detail": "Short code not found"},
        )
    return UrlInfoResponse(
        short_code=record.short_code,
        url=record.original_url,
        click_count=record.click_count,
        last_accessed=record.last_accessed,
        referrer=record.referrer,
        created_at=record.created_at,
        expires_at=record.expires_at,
        is_active=record.is_active,
    )


@router.delete(
    "/api/urls/{code}",
    status_code=204,
    summary="Delete a short URL",
    description="REQ-SHORT-006",
)
def delete_short_url(code: str, db: Session = Depends(get_db)):
    """
    REQ-SHORT-006: DELETE /api/urls/{code} → 204 on success, 404 if not found.
    Performs a soft delete (is_active = False) to preserve audit trail.
    """
    deleted = delete_url(db, code)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "detail": "Short code not found"},
        )
