# Spec-Driven Feature Factory — URL Shortener Service

**Assignment 2 | Claude Code: AI-Augmented Software Engineering**  
**Spec:** SPEC-SHORT-001 v1.0.0

A URL shortening service built **spec-first** — every line of code answers to a documented requirement. Demonstrates spec-driven development (SDD), YAML prompt engineering, schema-enforced AI output, and self-critique loops.

---

## Quick Start

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn src.main:app --reload

# Run tests
python -m pytest tests/ -v
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Repository Structure

```
├── prompts/                    # YAML prompt templates (AI instruction library)
│   ├── spec-writer.yaml        # Converts feature requests to formal specs
│   ├── architect.yaml          # Generates implementation plans from specs
│   ├── code-reviewer.yaml      # OWASP security review with structured output
│   └── test-generator.yaml     # Auto-generates tests from Gherkin scenarios
│
├── specs/                      # Formal specifications
│   ├── url-shortener.yaml      # SPEC-SHORT-001 — full spec with REQ-IDs, Gherkin, API contract
│   └── diagrams/               # Mermaid diagrams
│       ├── sequence.md         # URL shortening and redirect flow
│       ├── er.md               # Entity-relationship data model
│       └── state.md            # URL lifecycle state machine
│
├── src/                        # Implementation (every file cites REQ-IDs)
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy engine and session factory
│   ├── models.py               # ORM models (ShortenedUrl, Blocklist)
│   ├── schemas.py              # Pydantic request/response schemas + JSON schema
│   ├── crud.py                 # Database operations (create, read, delete, analytics)
│   ├── utils.py                # URL validation, SSRF prevention, code generation
│   └── routers/
│       └── urls.py             # HTTP route handlers
│
├── tests/                      # Auto-generated test suite (46 tests, 100% pass)
│   ├── conftest.py             # Fixtures (test DB, test client)
│   ├── test_url_shortening.py  # POST /urls — REQ-SHORT-001, 005, 006
│   ├── test_redirect.py        # GET /{code} — REQ-SHORT-002, 004
│   ├── test_analytics.py       # Analytics — REQ-SHORT-003
│   ├── test_expiry.py          # Expiry — REQ-SHORT-004
│   ├── test_validation.py      # URL validation unit tests — REQ-SHORT-005
│   └── test_api.py             # API contract — REQ-SHORT-006
│
├── docs/
│   ├── traceability-matrix.md  # REQ → code → test → pass/fail
│   └── self-critique-log.md    # Generate → Review → Fix cycles (2 cycles, 4 bugs found)
│
├── Lessons/                    # Educational lessons (lesson-gen)
│   ├── 00_Index.md             # Lesson index
│   ├── Lesson01_Spec_Driven_Development.md
│   ├── Lesson02_SQLAlchemy_FastAPI_Data_Layer.md
│   └── Lesson03_SSRF_URL_Validation.md
│
├── REPORT.md                   # Written answers to all 12 assignment questions
├── SECURITY.md                 # Security policy and vulnerability reporting
├── requirements.txt            # Pinned Python dependencies
└── README.md                   # This file
```

---

## API Endpoints

| Method | Path | Description | REQ-ID |
|--------|------|-------------|--------|
| `POST` | `/urls` | Shorten a URL | REQ-SHORT-001, 004, 005 |
| `GET` | `/{code}` | Redirect to original URL | REQ-SHORT-002, 003, 004 |
| `GET` | `/api/urls/{code}` | Get URL info and analytics | REQ-SHORT-003, 006 |
| `DELETE` | `/api/urls/{code}` | Delete a short URL | REQ-SHORT-006 |
| `GET` | `/api/health` | Health check | REQ-SHORT-006 |
| `GET` | `/docs` | Interactive OpenAPI UI | REQ-SHORT-006 |

---

## Test Results

```
46 tests collected
46 passed / 0 failed (100% pass rate)
First-run pass rate: 91.3% (42/46) — 4 failures caught by self-critique cycle
```

Run: `.\.venv\Scripts\python -m pytest tests/ -v`

---

## Security Features

- **SSRF prevention** — blocks private IP ranges (RFC 1918, loopback, 169.254.x.x)
- **Domain blocklist** — configurable malicious domain list with subdomain matching
- **Scheme validation** — only `http://` and `https://` accepted
- **Input length limit** — URLs over 2048 characters rejected
- **Soft deletion** — audit trail preserved when URLs are removed
- **Audit logging** — all creation, validation failures, and redirects logged

See `SECURITY.md` for vulnerability reporting.

---

## Assignment Context

Built for Week 2 of *Claude Code: AI-Augmented Software Engineering*. Demonstrates:
- **Spec-driven development** — spec before code, Gherkin scenarios, REQ-ID traceability
- **YAML prompt engineering** — 4 versioned prompt templates with output schemas
- **Self-critique loop** — Generate → Review (OWASP) → Fix → Validate
- **Schema-enforced output** — JSON schema on API responses and AI-generated reviews
