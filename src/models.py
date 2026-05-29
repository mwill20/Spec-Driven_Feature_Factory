# REQ-SHORT-001, REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004, REQ-SHORT-005
# SQLAlchemy ORM models — schema defined in specs/url-shortener.yaml data_model section.

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from .database import Base


class ShortenedUrl(Base):
    __tablename__ = "shortened_urls"

    id = Column(Integer, primary_key=True, index=True)
    # REQ-SHORT-001: unique 6-char alphanumeric code
    short_code = Column(String(6), unique=True, nullable=False, index=True)
    # REQ-SHORT-002: original URL target for redirect
    original_url = Column(Text, nullable=False)
    # REQ-SHORT-005: SHA-256 hash for O(1) duplicate detection
    url_hash = Column(String(64), unique=True, nullable=False, index=True)
    # REQ-SHORT-003: analytics fields
    click_count = Column(Integer, nullable=False, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    referrer = Column(Text, nullable=True)
    # REQ-SHORT-004: optional expiry
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_active = Column(Boolean, nullable=False, default=True)


class Blocklist(Base):
    __tablename__ = "blocklist"

    id = Column(Integer, primary_key=True, index=True)
    # REQ-SHORT-005: malicious domain blocklist
    domain = Column(String(253), unique=True, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    added_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_active = Column(Boolean, nullable=False, default=True)
