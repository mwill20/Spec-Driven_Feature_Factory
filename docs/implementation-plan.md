# Implementation Plan — URL Shortener Service

**Generated using:** `prompts/architect.yaml` v1.0.0  
**Spec reference:** SPEC-SHORT-001 v1.0.0 (`specs/url-shortener.yaml`)  
**Plan ID:** PLAN-SHORT-001  
**Tech Stack:** Python 3.12 + FastAPI 0.115.5 + SQLAlchemy 2.0.36 + SQLite + pytest

---

## Component Breakdown

| Component | File | Responsibility | REQ References |
|-----------|------|---------------|----------------|
| Database Engine | `src/database.py` | SQLAlchemy engine creation, session factory, `get_db()` dependency | All |
| ORM Models | `src/models.py` | `ShortenedUrl` and `Blocklist` table definitions | REQ-SHORT-001–005 |
| CRUD Operations | `src/crud.py` | All database read/write operations (no SQL in routers) | REQ-SHORT-001–006 |
| URL Utilities | `src/utils.py` | Code generation, SHA-256 hashing, URL validation, SSRF prevention | REQ-SHORT-001, 005 |
| Pydantic Schemas | `src/schemas.py` | Request/response validation, JSON schema definition | REQ-SHORT-001, 003, 004, 006 |
| URL Router | `src/routers/urls.py` | HTTP endpoints: POST /urls, GET /{code}, GET/DELETE /api/urls/{code} | REQ-SHORT-001–006 |
| App Entry Point | `src/main.py` | FastAPI app, lifespan (DB init, blocklist seed), health endpoint | REQ-SHORT-006 |

---

## Data Model

### Entity: `shortened_urls`

| Field | Type | Constraints | REQ-ID |
|-------|------|-------------|--------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | — |
| `short_code` | VARCHAR(6) | UNIQUE, NOT NULL, INDEX | REQ-SHORT-001 |
| `original_url` | TEXT | NOT NULL | REQ-SHORT-002 |
| `url_hash` | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | REQ-SHORT-005 |
| `click_count` | INTEGER | NOT NULL, DEFAULT 0 | REQ-SHORT-003 |
| `last_accessed` | DATETIME | NULLABLE | REQ-SHORT-003 |
| `referrer` | TEXT | NULLABLE | REQ-SHORT-003 |
| `expires_at` | DATETIME | NULLABLE | REQ-SHORT-004 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW() | — |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | REQ-SHORT-006 |

### Entity: `blocklist`

| Field | Type | Constraints | REQ-ID |
|-------|------|-------------|--------|
| `id` | INTEGER | PRIMARY KEY | — |
| `domain` | VARCHAR(253) | UNIQUE, NOT NULL, INDEX | REQ-SHORT-005 |
| `reason` | TEXT | NULLABLE | — |
| `added_at` | DATETIME | NOT NULL | — |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | — |

---

## Numbered Implementation Tasks

### TASK-001 — Database and ORM Foundation
**REQ References:** REQ-SHORT-001, REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004, REQ-SHORT-005  
**Files:** `src/database.py`, `src/models.py`  
**Estimated effort:** 30 min  
**Acceptance criteria:**
- `Base.metadata.create_all(engine)` creates `shortened_urls` and `blocklist` tables
- `get_db()` yields a session and closes it in a `finally` block
- `ShortenedUrl.url_hash` has a UNIQUE constraint
- `ShortenedUrl.short_code` is VARCHAR(6)

### TASK-002 — URL Validation and Code Generation
**REQ References:** REQ-SHORT-001, REQ-SHORT-005  
**Files:** `src/utils.py`  
**Estimated effort:** 30 min  
**Acceptance criteria:**
- `generate_short_code()` returns exactly 6 chars from `[a-zA-Z0-9]`
- `validate_url()` raises `UrlValidationError` for: non-http(s) scheme, private IPs, blocked domains, malformed URLs
- Private IP check uses `try/except/else` to prevent exception inheritance bypass
- `hash_url()` returns SHA-256 hex digest of lowercased+stripped URL

### TASK-003 — Pydantic Schemas and JSON Schema
**REQ References:** REQ-SHORT-001, REQ-SHORT-004, REQ-SHORT-006  
**Files:** `src/schemas.py`  
**Estimated effort:** 20 min  
**Acceptance criteria:**
- `UrlCreateRequest` validates `url` (max 2048 chars) and optional `expires_at`
- `UrlCreateResponse` includes `short_code`, `short_url`, `url`, `created_at`, `already_exists`
- `URL_CREATE_RESPONSE_SCHEMA` JSON schema enforces `short_code` pattern `^[a-zA-Z0-9]{6}$`
- `ErrorResponse` includes `status_code`, `error`, `detail` fields

### TASK-004 — CRUD Operations
**REQ References:** REQ-SHORT-001, REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004, REQ-SHORT-005, REQ-SHORT-006  
**Files:** `src/crud.py`  
**Estimated effort:** 30 min  
**Acceptance criteria:**
- `create_short_url()` deduplicates via `url_hash` lookup before inserting
- `create_short_url()` returns `(record, already_existed: bool)`
- `record_redirect()` increments `click_count`, updates `last_accessed`, stores `referrer`
- `delete_url()` sets `is_active = False` (soft delete)
- `get_blocked_domains()` loads active rows from `blocklist` table

### TASK-005 — HTTP Router (Endpoints)
**REQ References:** REQ-SHORT-001–006  
**Files:** `src/routers/urls.py`  
**Estimated effort:** 40 min  
**Acceptance criteria:**
- `POST /urls` → calls `validate_url()`, then `create_short_url()`; returns 201 (new) or 200 (existing)
- `GET /{code}` → checks expiry at request time (normalize naive datetime), calls `record_redirect()`, returns 302
- `GET /{code}` with expired URL → returns 410 without incrementing `click_count`
- `GET /api/urls/{code}` → returns analytics without redirecting
- `DELETE /api/urls/{code}` → soft delete, returns 204

### TASK-006 — App Entry Point and Lifespan
**REQ References:** REQ-SHORT-006  
**Files:** `src/main.py`  
**Estimated effort:** 20 min  
**Acceptance criteria:**
- `lifespan()` creates DB tables and seeds blocklist on startup
- `GET /api/health` returns 200 with `{status, version, timestamp}`
- All error responses include `X-Content-Type-Options: nosniff` header
- Unhandled exceptions return 500 without leaking internal details

### TASK-007 — Test Suite Generation
**REQ References:** All  
**Files:** `tests/`  
**Estimated effort:** 40 min  
**Acceptance criteria:**
- At least one test per Gherkin scenario (SCN-001–SCN-010)
- All 6 REQ-IDs covered by at least 2 tests each
- Unit tests for `generate_short_code()`, `hash_url()`, `validate_url()`
- Integration tests use `TestClient` with in-memory SQLite DB
- 100% pass rate after self-critique fixes

### TASK-008 — Documentation and Traceability
**REQ References:** All  
**Files:** `docs/traceability-matrix.md`, `docs/self-critique-log.md`, `REPORT.md`  
**Estimated effort:** 55 min  
**Acceptance criteria:**
- Traceability matrix covers all 6 REQ-IDs and 10 scenarios
- Self-critique log documents at minimum 2 review cycles with findings table
- REPORT.md answers all 12 assignment questions

---

## Dependency Installation

```bash
pip install fastapi==0.115.5 uvicorn==0.32.1 sqlalchemy==2.0.36 \
  pydantic==2.10.3 pydantic-settings==2.6.1 httpx==0.28.0 \
  pytest==8.3.4 pytest-asyncio==0.24.0 python-multipart==0.0.12 \
  validators==0.34.0
```

## Directory Layout

```
src/
├── __init__.py
├── main.py          # TASK-006
├── database.py      # TASK-001
├── models.py        # TASK-001
├── schemas.py       # TASK-003
├── crud.py          # TASK-004
├── utils.py         # TASK-002
└── routers/
    ├── __init__.py
    └── urls.py      # TASK-005
tests/
├── __init__.py
├── conftest.py
├── test_url_shortening.py
├── test_redirect.py
├── test_analytics.py
├── test_expiry.py
├── test_validation.py
└── test_api.py
```
