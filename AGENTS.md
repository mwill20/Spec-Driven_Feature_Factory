# AGENTS.md — AI Agent Behavior Instructions

This file governs how AI coding assistants (Claude Code, Codex, Copilot, etc.) should behave when working in this repository.

---

## Project Context

This is a **spec-driven** codebase. The specification in `specs/url-shortener.yaml` is the source of truth. Every change must trace back to a requirement ID (REQ-SHORT-NNN).

---

## Mandatory Rules

### 1. Spec Before Code
- Do not implement any feature not present in `specs/url-shortener.yaml`
- If a requested change requires a new requirement, add it to the spec first, then implement
- Never silently extend behavior beyond what the spec defines

### 2. Requirement ID Traceability
- Every modified or new source file MUST include a comment citing the relevant REQ-ID(s):
  ```python
  # REQ-SHORT-001, REQ-SHORT-005
  ```
- Every new test function MUST include a docstring with:
  ```python
  """
  REQ-ID: REQ-SHORT-NNN | Scenario: SCN-NNN | Type: happy_path|error_case|edge_case
  [One-line description of what this test proves]
  """
  ```

### 3. Security Defaults (Never Bypass)
- All URL submissions MUST pass through `src/utils.py:validate_url()` before database writes
- Never add a bypass, skip, or `trusted=True` flag that circumvents URL validation
- Never expose `id`, `url_hash`, or internal database fields in API responses
- Never hardcode credentials — all secrets via environment variables

### 4. Test Coverage
- Any new feature or bugfix MUST have a corresponding test
- Test must be in the appropriate file under `tests/`
- Run `.\.venv\Scripts\python -m pytest tests/ -v` before declaring work complete
- All 46 existing tests must continue to pass

### 5. CRUD Boundary
- Database queries (`db.query(...)`) belong ONLY in `src/crud.py`
- Route handlers in `src/routers/urls.py` call CRUD functions — they never query the DB directly

### 6. Error Responses
- All error responses MUST use the `ErrorResponse` schema: `{status_code, error, detail}`
- Never expose stack traces, internal paths, or exception messages in HTTP error responses

---

## Prohibited Actions

- Adding new endpoints without a corresponding REQ-ID in the spec
- Deleting tests to make the suite pass
- Removing the `is_active` soft-delete filter from any SELECT query
- Bypassing `validate_url()` for "trusted" or "internal" submissions
- Using `random.random()` or `random.choice()` for code generation (must use `random.SystemRandom()`)

---

## Validation Command

```powershell
.\.venv\Scripts\python -m pytest tests/ -v
```

Expected: 46 passed, 0 failed.

---

## File Ownership Map

| Change Type | Files to Touch |
|-------------|---------------|
| New endpoint | `specs/url-shortener.yaml` → `src/routers/urls.py` → `src/crud.py` (if DB needed) → `tests/test_api.py` |
| New validation rule | `specs/url-shortener.yaml` → `src/utils.py` → `tests/test_validation.py` |
| New data field | `specs/url-shortener.yaml` → `src/models.py` → `src/schemas.py` → `src/crud.py` → affected tests |
| Analytics change | `src/crud.py:record_redirect()` → `tests/test_analytics.py` |
