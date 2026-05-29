# REQ-SHORT-001, REQ-SHORT-003, REQ-SHORT-004, REQ-SHORT-006
# Pydantic v2 request/response schemas — enforces the API contract from
# specs/url-shortener.yaml api_contract section.

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class UrlCreateRequest(BaseModel):
    # REQ-SHORT-001, REQ-SHORT-005: accepts valid URL, max 2048 chars
    url: str = Field(..., max_length=2048, description="Valid HTTP or HTTPS URL")
    # REQ-SHORT-004: optional expiry datetime
    expires_at: Optional[datetime] = Field(
        None, description="Optional ISO 8601 UTC expiration datetime"
    )

    @field_validator("url")
    @classmethod
    def url_must_be_string(cls, v: str) -> str:
        return v.strip()


class UrlCreateResponse(BaseModel):
    short_code: str
    short_url: str
    url: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    already_exists: bool = False

    model_config = {"from_attributes": True}


class UrlInfoResponse(BaseModel):
    # REQ-SHORT-003: analytics fields
    short_code: str
    url: str
    click_count: int
    last_accessed: Optional[datetime] = None
    referrer: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    # REQ-SHORT-006: structured error format required on all endpoints
    status_code: int
    error: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


# JSON schema for --json-schema enforcement (used in self-critique loop)
# This is the schema Claude validates its structured output against.
URL_CREATE_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["short_code", "short_url", "url", "created_at"],
    "properties": {
        "short_code": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9]{6}$",
            "description": "Exactly 6 alphanumeric characters (REQ-SHORT-001)",
        },
        "short_url": {"type": "string", "format": "uri"},
        "url": {"type": "string", "format": "uri"},
        "expires_at": {"type": ["string", "null"], "format": "date-time"},
        "created_at": {"type": "string", "format": "date-time"},
        "already_exists": {"type": "boolean"},
    },
    "additionalProperties": False,
}
