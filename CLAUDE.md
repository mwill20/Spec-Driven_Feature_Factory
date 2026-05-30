# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Activate virtual environment (required before all other commands)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn src.main:app --reload

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_validation.py -v

# Run a single test by name
python -m pytest tests/test_validation.py -k "test_reject_private_ip" -v

# Run tests matching a requirement ID
python -m pytest tests/ -k "test_shorten" -v
```

API available at `http://localhost:8000` | Docs at `http://localhost:8000/docs`

## Architecture

**Spec-driven:** `specs/url-shortener.yaml` (SPEC-SHORT-001) is the source of truth. Every source file cites REQ-IDs in comments; every test function cites them in docstrings. The traceability chain is `spec → code → test → traceability-matrix.md`.

**Layer structure:**

```
Request → src/routers/urls.py  (HTTP only: status codes, error mapping)
              ↓              ↘
        src/utils.py         src/crud.py  (all db.query() lives here)
        (validation,              ↓
         SSRF, codegen)      src/models.py (ORM)
                                  ↓
                             SQLite (via src/database.py)
```

The CRUD boundary is enforced: routers call named CRUD functions and never write raw `db.query()` calls. Violating this spreads persistence logic across the HTTP layer.

**Security-relevant invariants:**

- `src/utils.py:validate_url()` uses `try/except/else` — not `try/except` — because `UrlValidationError` inherits from `ValueError`. A broad `except ValueError` silently swallows the SSRF check. This is FIND-001 from `docs/self-critique-log.md`; do not change this pattern.
- Expiry is evaluated at request time in `redirect_to_url()`, not stored as a flag. The datetime comparison normalizes SQLite's naive datetimes with `.replace(tzinfo=timezone.utc)` before comparing to `datetime.now(timezone.utc)`. This is FIND-002; both sides must be timezone-aware.
- Deletion is always soft (`is_active = False`). Never use `DELETE FROM shortened_urls` — the audit trail must be preserved.
- `src/schemas.py:URL_CREATE_RESPONSE_SCHEMA` has `"additionalProperties": false`. This prevents internal fields (`id`, `url_hash`) from leaking in API responses. Do not add fields to `UrlCreateResponse` without checking they belong in the public contract.

**Prompt library:** `prompts/` contains 4 versioned YAML templates (spec-writer, architect, code-reviewer, test-generator). These are the AI instruction sets that generated the spec, implementation plan, review cycle, and test suite. They are versioned alongside code.

## Key Files

| File | Role |
|------|------|
| `specs/url-shortener.yaml` | Authoritative spec — REQ-SHORT-001 through 006, 10 Gherkin scenarios, API contract, NFRs |
| `docs/implementation-plan.md` | TASK-NNN breakdown with per-task acceptance criteria — use when adding new features |
| `docs/self-critique-log.md` | REV-001/REV-002 findings — read before touching `src/utils.py` or `src/routers/urls.py` |
| `docs/traceability-matrix.md` | REQ → code → test → status — update when adding new requirements or tests |
| `AGENTS.md` | Mandatory rules for AI assistants in this repo (spec-before-code, prohibited actions, file ownership map) |

## Adding a New Feature

1. Add a `REQ-SHORT-NNN` entry to `specs/url-shortener.yaml` with acceptance criteria and at least one Gherkin scenario
2. Update `docs/traceability-matrix.md` with the new REQ-ID row (status: PENDING)
3. Add `TASK-NNN` to `docs/implementation-plan.md` with measurable acceptance criteria
4. Implement — cite the new REQ-ID in every modified file
5. Add tests in the appropriate `tests/test_*.py` file; each test docstring must include `REQ-ID: REQ-SHORT-NNN | Scenario: SCN-NNN | Type: happy_path|error_case|edge_case`
6. Run `.\.venv\Scripts\python -m pytest tests/ -v` — all 46 existing tests must continue to pass
7. Update `docs/traceability-matrix.md` status to PASS
