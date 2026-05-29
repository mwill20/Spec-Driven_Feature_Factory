# 🎓 Lesson 02: The Vault and the Ledger — SQLAlchemy + FastAPI Data Layer

## 🛡️ Welcome Back, Security Analyst!

In a SIEM investigation, you pull raw logs from a data source, normalize them, enrich them with threat intel, and write the result to a case. You never write a SQL query directly in the middle of your playbook — the data layer is abstracted away. 🔍 Today we're exploring the **SQLAlchemy + FastAPI data layer** (`src/database.py`, `src/models.py`, `src/crud.py`, `src/routers/urls.py`) — the "vault and ledger" that stores every shortened URL, tracks every redirect, and keeps the HTTP layer completely separate from the persistence layer.

---

## 🎯 Learning Objectives

By the end of this lesson you will be able to:

- Explain how SQLAlchemy ORM models translate to database tables
- Trace a POST /urls request through FastAPI's dependency injection into the database and back out
- Describe why the CRUD layer exists as a separate module from the router
- Identify the timezone normalization pattern and explain why it matters for SQLite
- Read SQLAlchemy query syntax and predict what SQL it generates

**Time estimate:** 50 minutes | **Prerequisites:** Lesson 01

---

## 🧠 What This Component Does — Plain English

FastAPI handles HTTP — it receives requests, validates them against Pydantic schemas, and returns responses. But it doesn't know how to talk to a database. SQLAlchemy handles database persistence — it translates Python object operations into SQL. The bridge between them is a pattern called **dependency injection**: FastAPI creates a database session, injects it into the route handler, and closes it when the handler returns.

The CRUD layer (`src/crud.py`) sits between the router and the database. It owns all SQL operations. The router never writes a `db.query()` call directly — it calls named functions like `create_short_url()` or `record_redirect()`. This separation means: if you switch databases (SQLite → PostgreSQL), you change `src/database.py` and `src/crud.py`, not the router. The router doesn't know or care whether URLs are stored in SQLite, PostgreSQL, or a Redis cache.

**Real-world analogy:** In Swimlane, your SOAR playbook calls action steps like "Enrich IOC" or "Create Case" — it doesn't embed raw API calls inline. The action step is a named, reusable operation that hides the underlying API details. `create_short_url()` in this project is the same thing: a named operation with a clear contract (`url` in, `(ShortenedUrl, bool)` out) that hides all the SQL.

---

## 🗺️ Where This Fits in the System

```
🌐 HTTP Request (POST /urls, GET /{code})
        ↓
📋 FastAPI Router (src/routers/urls.py) — validates Pydantic schema
        ↓
🔒 Dependency Injection — db: Session = Depends(get_db)   ← (THIS LESSON)
        ↓
📦 CRUD Layer (src/crud.py) — all database operations      ← (THIS LESSON)
        ↓
🏗️ SQLAlchemy ORM Models (src/models.py)                   ← (THIS LESSON)
        ↓
💾 SQLite Database (url_shortener.db)
```

If the CRUD layer is removed and routers talk directly to the database, any schema change requires updating every router that touches that table — instead of one CRUD function.

---

## 🔑 Key Concepts

### SQLAlchemy ORM

An Object-Relational Mapper translates Python class definitions into database table definitions. When you define a Python class that inherits from `Base` and has `Column` fields, SQLAlchemy knows how to `CREATE TABLE`, `INSERT`, `SELECT`, and `UPDATE` without you writing SQL. This is the same principle as using an IOC enrichment adapter that abstracts whether you're calling VirusTotal or Abuse.ch — the calling code doesn't change when the backend changes.

### Dependency Injection in FastAPI

FastAPI's `Depends()` system automatically runs a setup function, passes its return value to the route handler, and runs cleanup when the handler finishes. `get_db()` in `src/database.py` opens a database session, yields it, and closes it in a `finally` block — guaranteeing the connection is always released even if an exception occurs. This is the same pattern as Python's `with` statement for file handles, but declarative rather than explicit.

### Soft Delete

When a URL is "deleted" in this system, `is_active` is set to `False` — the row stays in the database. This preserves the audit trail: you can always query what URLs existed, when they were created, and how many times they were accessed, even after deletion. Hard deletes are permanent and unrecoverable; soft deletes are reversible and forensically complete.

### Naive vs. Aware Datetimes

Python's `datetime` objects come in two flavors: naive (no timezone information) and aware (explicit timezone). SQLite stores datetimes as text without timezone info — when SQLAlchemy reads them back, they become naive datetimes. `datetime.now(timezone.utc)` is always aware. Comparing naive to aware raises a `TypeError`. The fix is to normalize: if a datetime has no `tzinfo`, attach UTC. This is the timezone issue caught in the self-critique cycle (FIND-002 in `docs/self-critique-log.md`).

---

## 📝 Code Walkthrough

### The Database Engine and Session Factory

```python
# src/database.py — Lines 1–18
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./url_shortener.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Line-by-line breakdown:**

| Lines | What it does | Why it was designed this way |
|-------|-------------|------------------------------|
| `DATABASE_URL = os.getenv(...)` | Reads DB URL from environment variable with SQLite fallback | REQ-NFR-SECURITY: no hardcoded credentials. Swapping to PostgreSQL requires only `DATABASE_URL=postgres://...` — no code change |
| `check_same_thread: False` | SQLite-specific: allows multiple threads to use the same connection | FastAPI runs route handlers in threads; without this flag, SQLite raises "SQLite objects created in a thread can only be used in that same thread" |
| `autocommit=False, autoflush=False` | Explicit transaction control | Prevents partial writes from auto-committing before the operation is complete. Every `db.commit()` in `crud.py` is intentional |
| `yield db` in `get_db()` | Generator-based cleanup pattern | The `yield` makes this a context manager. FastAPI calls the generator, gets `db`, passes it to the handler, then resumes after `yield` to run the `finally` block |

### The ORM Model — ShortenedUrl

```python
# src/models.py — Lines 14–42
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
```

**Design decisions visible in this model:**

- `url_hash = Column(String(64), unique=True, ...index=True)` — SHA-256 is 64 hex characters. `unique=True` enforces deduplication at the database level (not just application level), meaning even if a bug bypassed the application check, the database would reject the duplicate. `index=True` makes hash lookups O(log n) instead of O(n).
- `expires_at = Column(DateTime(timezone=True), nullable=True)` — nullable because expiry is optional (REQ-SHORT-004). `timezone=True` tells SQLAlchemy to attempt timezone-aware storage, though SQLite's text storage still returns naive datetimes on read.
- `is_active = Column(Boolean, ..., default=True)` — the soft-delete flag. Filtered on every `SELECT` via `ShortenedUrl.is_active == True`.

> ⚠️ **Common pitfall:** `DateTime(timezone=True)` in SQLAlchemy with SQLite does **not** guarantee timezone-aware datetimes on read. SQLite stores datetimes as ISO 8601 text strings without timezone suffixes. When SQLAlchemy reads them back, Python gets a naive datetime. Always normalize before comparing: `if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)`.

### The CRUD Layer — create_short_url

```python
# src/crud.py — Lines 37–73
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
```

**The `for/else` pattern (Python-specific):**

Python's `for/else` runs the `else` block only if the `for` loop completes without hitting a `break`. This is used here to detect exhaustion: if all 10 retries produce codes that already exist in the database (astronomically rare — 62^6 ≈ 56 billion possibilities), the `else` block raises `RuntimeError`. This is safer than a `while True` loop with a counter because the failure case is explicit and named.

**The deduplication pattern:**

```
1. hash_url(original_url) → SHA-256 digest
2. SELECT WHERE url_hash = digest → found? return existing record
3. NOT found → generate new code, INSERT new record
```

This pattern handles the idempotency requirement (SCN-008) at the database layer, not just the application layer. Even if two concurrent requests submit the same URL simultaneously, the `unique=True` constraint on `url_hash` ensures only one INSERT succeeds; the second gets a unique constraint violation.

### The Redirect Endpoint — Expiry Check

```python
# src/routers/urls.py — Lines 129–139
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
```

This is the fix for FIND-002 from the self-critique cycle. The normalization pattern:
1. Read `record.expires_at` — may be naive (SQLite) or aware (PostgreSQL)
2. If naive, attach UTC via `.replace(tzinfo=timezone.utc)` — this doesn't convert the time, it labels it
3. Compare to `datetime.now(timezone.utc)` — both are now aware, comparison is valid

The expiry is evaluated **at redirect time**, not stored as a flag. This means a URL that expires at 3:00 PM will redirect successfully at 2:59 PM and return 410 at 3:01 PM without any background job or scheduled update. This is a deliberate design choice that trades accuracy (always checked against the real clock) for simplicity (no cron jobs, no race conditions between the flag-update job and the redirect handler).

---

## 🧪 Hands-On Exercises

> Activate the virtual environment: `.\.venv\Scripts\Activate.ps1`

### 🔬 Exercise 1: Inspect the Live Database Schema

After running the tests, a `test_url_shortener.db` file exists. Inspect its schema.

```powershell
python -c "
import sqlite3
conn = sqlite3.connect('test_url_shortener.db')
cursor = conn.cursor()
cursor.execute(\"SELECT sql FROM sqlite_master WHERE type='table'\")
for row in cursor.fetchall():
    print(row[0])
    print()
conn.close()
"
```

📊 **Expected output (abbreviated):**
```
CREATE TABLE shortened_urls (
    id INTEGER NOT NULL,
    short_code VARCHAR(6) NOT NULL,
    original_url TEXT NOT NULL,
    url_hash VARCHAR(64) NOT NULL,
    click_count INTEGER NOT NULL,
    last_accessed DATETIME,
    referrer TEXT,
    expires_at DATETIME,
    created_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL,
    PRIMARY KEY (id)
)

CREATE TABLE blocklist (
    id INTEGER NOT NULL,
    domain VARCHAR(253) NOT NULL,
    ...
)
```

✅ **You succeeded if:** You see `short_code VARCHAR(6)` (matches `String(6)` in the model) and `url_hash VARCHAR(64)` (matches SHA-256 hex length), confirming the ORM translated the model exactly.

---

### 🔬 Exercise 2: Trace a URL Through the Full Stack

This exercise traces a single POST /urls request from the test client to the database.

```powershell
python -c "
from tests.conftest import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.crud import create_short_url, get_url_by_hash
from src.utils import hash_url

# Set up in-memory DB
engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# Step 1: create a URL
url = 'https://www.example.com/trace-test'
record, already_existed = create_short_url(db, url)
print('Created:', record.short_code, '| already_existed:', already_existed)

# Step 2: prove the hash is stored
stored_hash = record.url_hash
expected_hash = hash_url(url)
print('Hash matches:', stored_hash == expected_hash)

# Step 3: look it up by hash
found = get_url_by_hash(db, expected_hash)
print('Retrieved by hash:', found.short_code, '| url:', found.original_url)

# Step 4: submit same URL again — proves idempotency
record2, already_existed2 = create_short_url(db, url)
print('Second submission code:', record2.short_code, '| already_existed:', already_existed2)
print('Same code returned:', record.short_code == record2.short_code)
"
```

📊 **Expected output:**
```
Created: [6-char code]  | already_existed: False
Hash matches: True
Retrieved by hash: [same code]  | url: https://www.example.com/trace-test
Second submission code: [same code]  | already_existed: True
Same code returned: True
```

✅ **You succeeded if:** The second submission returns `already_existed: True` and the same short code — proving SCN-008 (idempotency) works at the CRUD layer.

---

### 🔬 Exercise 3: Intentional Failure — Database Constraint Violation

This exercise shows what happens when the unique constraint on `url_hash` is violated at the database level.

```powershell
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from src.database import Base
from src.models import ShortenedUrl
from src.utils import hash_url

engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

url = 'https://www.example.com/constraint-test'
h = hash_url(url)

r1 = ShortenedUrl(short_code='aaa111', original_url=url, url_hash=h)
db.add(r1)
db.commit()
print('First insert: OK')

# Attempt to insert same url_hash with a different code
r2 = ShortenedUrl(short_code='bbb222', original_url=url, url_hash=h)
db.add(r2)
try:
    db.commit()
    print('Second insert: should not reach here')
except IntegrityError as e:
    db.rollback()
    print('Second insert: IntegrityError (expected) —', type(e).__name__)
    print('This proves the database enforces deduplication independently of the app layer.')
"
```

📊 **Expected output:**
```
First insert: OK
Second insert: IntegrityError (expected) — IntegrityError
This proves the database enforces deduplication independently of the app layer.
```

✅ **You succeeded if:** The second insert raises `IntegrityError` — proving that even a bug in the application layer that bypassed the hash lookup would be caught by the database constraint.

---

## 📚 Interview Preparation

### Q: Why use a CRUD layer instead of putting database calls directly in the router?

**A:** The router's responsibility is HTTP: deserialize the request, call the right operation, serialize the response, return the right status code. The database's responsibility is persistence. Mixing them means that to change how data is stored (adding a field, switching databases, adding a cache), you have to modify the HTTP handling code. By putting all `db.query()` calls in `crud.py`, any storage change is isolated to one module. The router stays stable even if the database schema evolves. This is the separation of concerns principle — the same reason a Swimlane playbook separates "enrich IOC" (data operation) from "send notification" (communication operation).

*Why this answer works:* It applies a concrete design principle and maps it to a familiar analogy.

---

### Q: Why does `create_short_url()` return `(ShortenedUrl, bool)` instead of raising an exception when a URL already exists?

**A:** A duplicate URL is not an error — it's valid business behavior (SCN-008: idempotent submission). Using an exception for it would force callers to use try/except for normal control flow, which is an anti-pattern. Returning a tuple `(record, already_existed)` lets the caller decide whether to respond with 201 (new) or 200 (existing) without exception handling. The router uses this: `status_code = 200 if already_exists else 201`. This keeps the CRUD layer ignorant of HTTP and the router ignorant of database semantics.

*Why this answer works:* It demonstrates understanding of exception semantics (errors vs. expected states) and clear interface design.

---

### Q: What security property does `is_active = Column(Boolean, ..., default=True)` enforce?

**A:** Soft deletion preserves the audit trail. Hard deleting a row removes the evidence that the URL ever existed, which means you can't answer post-incident questions like "was this short code used in a phishing campaign before it was deleted?" or "how many times was this URL accessed before we took it down?" With soft deletion, `is_active = False` excludes the record from redirect resolution while keeping the full click history, referrer data, and creation timestamp intact for forensic review. This is the same principle as marking an account as `disabled` in an IAM system rather than deleting it — you need the record for auditing even after the access is revoked.

*Why this answer works:* It connects a data model decision to a concrete security and forensic outcome.

---

## ✅ Key Takeaways

- SQLAlchemy ORM translates Python class definitions to SQL tables — `Column(String(6), unique=True)` becomes `short_code VARCHAR(6) UNIQUE` in the database
- FastAPI's `Depends(get_db)` pattern uses a generator to inject a database session and guarantee cleanup — even if the handler raises an exception
- The CRUD layer is a boundary: the router knows HTTP, the CRUD layer knows SQL, and neither crosses into the other's domain
- `DateTime(timezone=True)` in SQLAlchemy with SQLite does not guarantee timezone-aware datetimes on read — always normalize with `.replace(tzinfo=timezone.utc)` before comparing
- Soft deletion (`is_active = False`) preserves audit trails — critical for post-incident forensics

---

## 📋 Quick Reference Card

| Item | Value |
|------|-------|
| Database config | `src/database.py` |
| ORM models | `src/models.py` — `ShortenedUrl`, `Blocklist` |
| CRUD operations | `src/crud.py` |
| Entry points | `create_short_url()`, `record_redirect()`, `get_url_by_code()`, `delete_url()` |
| Session injection | `db: Session = Depends(get_db)` in any route handler |
| Key constraint | `url_hash VARCHAR(64) UNIQUE` — database-level deduplication |
| Soft delete field | `ShortenedUrl.is_active` — filtered on every SELECT |
| Timezone fix | `if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)` |
| Test file | `tests/test_analytics.py`, `tests/test_expiry.py`, `tests/test_redirect.py` |

---

## 📌 Implemented vs. Recommended

### What This Project Implements ✅
- SQLAlchemy ORM with typed columns and database-level constraints (`src/models.py`)
- Dependency-injected DB sessions with guaranteed cleanup (`src/database.py:get_db()`)
- Separate CRUD layer with named operations (`src/crud.py`)
- Soft delete with `is_active` flag (`src/crud.py:delete_url()`)
- Timezone normalization for SQLite compatibility (`src/routers/urls.py` lines 131–134)

### General Best Practices — Not Implemented Here
- **Alembic migrations** — version-controlled database schema changes with upgrade/downgrade scripts — `Recommended (not implemented here)`
- **Connection pooling** — `create_engine(..., pool_size=10, max_overflow=20)` for production load — `Recommended (not implemented here)`
- **Async SQLAlchemy** — `async_session` + `AsyncEngine` for fully async FastAPI routes — `Recommended (not implemented here)`

---

## 🚀 Ready for Lesson 03?

Next up: **The Steel Door — SSRF Prevention and URL Validation Security** — the most security-critical component in the service. You'll trace exactly how a malicious URL like `http://192.168.1.1/admin` is detected and blocked before it ever reaches the database, and discover the Python exception hierarchy trap that silently disabled the SSRF protection until the self-critique cycle caught it.

**Optional deeper dive:** Read the SQLAlchemy 2.0 session documentation on "2.0 style" queries — this project uses the older ORM query style (`db.query(Model).filter(...)`), and the newer style (`db.execute(select(Model).where(...))`) is worth understanding for new projects.

**Modification challenge:** Add a `visit_count_today` field to the `ShortenedUrl` model — an integer that resets to 0 daily. You'll need to add the column to `models.py`, update `record_redirect()` in `crud.py` to increment it, and add a test. Note: without Alembic, you'll need to delete `test_url_shortener.db` before re-running tests to let SQLAlchemy recreate the schema.

*Remember: the CRUD layer is your contract — change the storage, keep the interface.* 🛡️
