# Architecture — URL Shortener Service

**Spec:** SPEC-SHORT-001 v1.0.0  
**Stack:** Python 3.12 + FastAPI 0.115.5 + SQLAlchemy 2.0.36 + SQLite

---

## System Overview

A RESTful URL shortening service built spec-first. The system accepts long URLs, generates unique 6-character short codes, redirects users, tracks analytics, enforces expiry, and blocks malicious URLs via SSRF prevention and domain blocklist.

```
┌─────────────────────────────────────────────────────────┐
│                     Client (Browser / API)               │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                    FastAPI Application                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │          src/routers/urls.py (HTTP layer)         │   │
│  │  POST /urls · GET /{code} · GET/DELETE /api/...   │   │
│  └──────────┬─────────────────────────┬─────────────┘   │
│             │ validate                │ db ops           │
│  ┌──────────▼──────────┐  ┌──────────▼─────────────┐   │
│  │   src/utils.py      │  │     src/crud.py         │   │
│  │  URL validation     │  │  CRUD operations        │   │
│  │  SSRF prevention    │  │  dedup · analytics      │   │
│  │  code generation    │  │  expiry · soft-delete   │   │
│  └─────────────────────┘  └──────────┬──────────────┘   │
│                                       │ SQLAlchemy ORM    │
│  ┌────────────────────────────────────▼──────────────┐   │
│  │              src/models.py (ORM Models)            │   │
│  │        ShortenedUrl · Blocklist                    │   │
│  └────────────────────────────────────┬───────────────┘  │
└───────────────────────────────────────┼─────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │  SQLite Database    │
                              │  shortened_urls     │
                              │  blocklist          │
                              └────────────────────┘
```

---

## Component Descriptions

### `src/main.py` — App Entry Point
Initializes the FastAPI application, wires up the router, and runs the lifespan handler on startup (creates database tables, seeds the blocklist with default blocked domains). Registers global exception handlers that return structured `ErrorResponse` JSON without leaking internal details.

### `src/database.py` — Persistence Engine
Creates the SQLAlchemy engine from `DATABASE_URL` environment variable (defaults to SQLite). Provides `get_db()` — a generator used by FastAPI's dependency injection system to inject a scoped database session into each request handler and close it on completion.

### `src/models.py` — ORM Models
Defines two SQLAlchemy `Base` subclasses:
- `ShortenedUrl` — one row per shortened URL; tracks short code, original URL, SHA-256 hash (deduplication), click analytics, expiry, and active status
- `Blocklist` — one row per blocked domain; supports configurable malicious domain filtering

### `src/schemas.py` — Pydantic Validation Layer
Defines request/response shapes. `UrlCreateRequest` validates incoming URL and optional expiry. `UrlCreateResponse` defines the API response contract. `URL_CREATE_RESPONSE_SCHEMA` is the JSON Schema used for schema-enforced output validation (see `docs/schema-enforcement.md`).

### `src/utils.py` — Security Utilities
The security gatekeeper. `validate_url()` enforces: HTTP/HTTPS scheme only, parseable URI format, no private/reserved IPs (SSRF prevention), and configurable domain blocklist. Uses `try/except/else` to prevent exception inheritance from silently bypassing SSRF checks. `generate_short_code()` uses `random.SystemRandom()` (CSPRNG) for code generation.

### `src/crud.py` — Data Access Layer
All database operations isolated here. Routers never write raw SQLAlchemy queries. Key operations: `create_short_url()` (dedup via hash then insert), `record_redirect()` (analytics update), `delete_url()` (soft delete via `is_active = False`), `get_blocked_domains()` (blocklist load).

### `src/routers/urls.py` — HTTP Endpoints
Maps HTTP verbs to business operations. Handles status code selection (201 vs 200 for new vs existing URL), error code mapping from `UrlValidationError` to HTTP status, and the timezone normalization pattern for SQLite datetime comparison.

---

## Key Design Decisions

### 1. CRUD Boundary
All `db.query()` calls are in `src/crud.py`. Routers call named functions. This isolates the HTTP layer from the persistence layer — switching databases requires changes to `database.py` and `crud.py` only.

### 2. SHA-256 Deduplication
`url_hash = sha256(normalized_url)` is stored as a UNIQUE indexed column. Duplicate detection is O(log n) without full-text scan, and the database constraint provides a second layer of protection even if the application check is bypassed.

### 3. At-Request-Time Expiry
Expiry is evaluated when a redirect is requested, not stored as a flag. No background job needed — a URL with `expires_at` in the past will return 410 accurately to the clock without scheduled tasks or race conditions.

### 4. Soft Delete
`is_active = False` rather than `DELETE FROM`. Audit trail (creation timestamp, click count, referrer history) is preserved for forensic review after a URL is removed.

### 5. Configurable Blocklist
Blocked domains are stored in the `blocklist` table and loaded per-request. Default domains are seeded at startup. Operators can add new blocked domains at runtime by inserting a row — no code deployment required.

---

## Data Flow — POST /urls (Happy Path)

```
1. Client POSTs {"url": "https://long.example.com/path", "expires_at": null}
2. FastAPI deserializes via UrlCreateRequest (Pydantic validates max_length=2048)
3. shorten_url() router function called
4. get_blocked_domains(db) → loads active blocklist from DB
5. validate_url(url, blocked_domains) → checks scheme, format, private IP, blocklist
6. create_short_url(db, validated_url) → hash_url() → lookup by hash → not found
7. generate_short_code() → 6-char CSPRNG code
8. ShortenedUrl INSERT with short_code, original_url, url_hash
9. UrlCreateResponse built → JSON response 201 Created
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.115.5 | HTTP framework, OpenAPI generation |
| `uvicorn` | 0.32.1 | ASGI server |
| `sqlalchemy` | 2.0.36 | ORM and database abstraction |
| `pydantic` | 2.10.3 | Request/response schema validation |
| `pydantic-settings` | 2.6.1 | Environment variable configuration |
| `httpx` | 0.28.0 | HTTP client for TestClient |
| `pytest` | 8.3.4 | Test framework |
| `pytest-asyncio` | 0.24.0 | Async test support |
| `python-multipart` | 0.0.12 | Form data parsing |
| `validators` | 0.34.0 | URL validation utilities |
