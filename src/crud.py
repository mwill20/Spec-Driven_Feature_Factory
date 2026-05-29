# REQ-SHORT-001, REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004, REQ-SHORT-005
# Database CRUD operations — all DB access goes through this module.

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .models import Blocklist, ShortenedUrl
from .utils import generate_short_code, hash_url

_MAX_CODE_RETRIES = 10


def get_url_by_code(db: Session, code: str) -> Optional[ShortenedUrl]:
    """Retrieve a URL record by short code.
    REQ-SHORT-002: used by the redirect endpoint.
    """
    return (
        db.query(ShortenedUrl)
        .filter(ShortenedUrl.short_code == code, ShortenedUrl.is_active == True)
        .first()
    )


def get_url_by_hash(db: Session, url_hash: str) -> Optional[ShortenedUrl]:
    """Look up an existing URL by its SHA-256 hash.
    REQ-SHORT-005: idempotency — same URL returns the same code.
    """
    return (
        db.query(ShortenedUrl)
        .filter(ShortenedUrl.url_hash == url_hash, ShortenedUrl.is_active == True)
        .first()
    )


def create_short_url(
    db: Session,
    original_url: str,
    expires_at: Optional[datetime] = None,
) -> tuple[ShortenedUrl, bool]:
    """Create a new shortened URL or return the existing one.

    REQ-SHORT-001: generates unique 6-char code.
    REQ-SHORT-004: stores optional expiry.
    REQ-SHORT-005: deduplicates via url_hash.

    Returns (ShortenedUrl, already_existed).
    """
    url_hash = hash_url(original_url)

    existing = get_url_by_hash(db, url_hash)
    if existing:
        return existing, True

    # Generate a unique code, retrying on the rare collision
    for _ in range(_MAX_CODE_RETRIES):
        code = generate_short_code()
        if not db.query(ShortenedUrl).filter(ShortenedUrl.short_code == code).first():
            break
    else:
        raise RuntimeError("Failed to generate a unique short code after retries")

    record = ShortenedUrl(
        short_code=code,
        original_url=original_url,
        url_hash=url_hash,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, False


def record_redirect(
    db: Session, record: ShortenedUrl, referrer: Optional[str]
) -> None:
    """Update analytics after a successful redirect.
    REQ-SHORT-003: increments click_count, updates last_accessed and referrer.
    """
    record.click_count += 1
    record.last_accessed = datetime.now(timezone.utc)
    record.referrer = referrer
    db.commit()


def delete_url(db: Session, code: str) -> bool:
    """Soft-delete a short URL by setting is_active = False.
    REQ-SHORT-006: DELETE /api/urls/{code} endpoint support.
    Returns True if found and deleted, False if not found.
    """
    record = get_url_by_code(db, code)
    if not record:
        return False
    record.is_active = False
    db.commit()
    return True


def get_blocked_domains(db: Session) -> list[str]:
    """Load active blocked domains from the database.
    REQ-SHORT-005: configurable blocklist.
    """
    rows = db.query(Blocklist).filter(Blocklist.is_active == True).all()
    return [row.domain for row in rows]


def seed_blocklist(db: Session, domains: list[str]) -> None:
    """Seed the blocklist table with initial blocked domains.
    Called at application startup if the table is empty.
    """
    for domain in domains:
        if not db.query(Blocklist).filter(Blocklist.domain == domain).first():
            db.add(Blocklist(domain=domain, reason="Seeded at startup"))
    db.commit()
