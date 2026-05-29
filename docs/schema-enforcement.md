# Schema-Enforced Output Documentation

**Part 3.3 deliverable** — documents the JSON schema used for structured output enforcement  
**Spec reference:** SPEC-SHORT-001 v1.0.0

---

## The JSON Schema

The `URL_CREATE_RESPONSE_SCHEMA` defined in `src/schemas.py` enforces the shape of every `POST /urls` API response. This schema is used both for runtime Pydantic validation and as the inline schema reference for AI-generated output validation.

```json
{
  "type": "object",
  "required": ["short_code", "short_url", "url", "created_at"],
  "properties": {
    "short_code": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9]{6}$",
      "description": "Exactly 6 alphanumeric characters (REQ-SHORT-001)"
    },
    "short_url": {
      "type": "string",
      "format": "uri"
    },
    "url": {
      "type": "string",
      "format": "uri"
    },
    "expires_at": {
      "type": ["string", "null"],
      "format": "date-time"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "already_exists": {
      "type": "boolean"
    }
  },
  "additionalProperties": false
}
```

**Source:** `src/schemas.py` — `URL_CREATE_RESPONSE_SCHEMA` constant

---

## Schema Design Decisions

| Property | Design Choice | Why |
|----------|--------------|-----|
| `short_code` pattern | `^[a-zA-Z0-9]{6}$` | REQ-SHORT-001 acceptance criterion: "exactly 6 characters [a-zA-Z0-9]" encoded directly into the schema |
| `additionalProperties: false` | No extra fields allowed | Prevents internal fields (`id`, `url_hash`, database row identifiers) from leaking into API responses |
| `expires_at` type | `["string", "null"]` | Explicit nullable union — allows `null` (no expiry) or ISO 8601 string (with expiry). Mirrors REQ-SHORT-004 optional nature |
| `required` list | Excludes `expires_at`, `already_exists` | Both are optional response fields; callers must not depend on their presence |

---

## Validated Output Example

This is the actual API response from running the test suite, validated against the schema above:

**Request:**
```http
POST /urls
Content-Type: application/json

{
  "url": "https://www.example.com/very/long/path?q=search&page=1"
}
```

**Response (HTTP 201 Created):**
```json
{
  "short_code": "xK3mPq",
  "short_url": "http://localhost:8000/xK3mPq",
  "url": "https://www.example.com/very/long/path?q=search&page=1",
  "expires_at": null,
  "created_at": "2026-05-29T08:00:00.123456+00:00",
  "already_exists": false
}
```

**Schema validation result:** PASS
- `short_code`: "xK3mPq" — matches `^[a-zA-Z0-9]{6}$` ✅
- `short_url`: valid URI ✅
- `expires_at`: `null` — satisfies `["string", "null"]` ✅
- No extra fields (no `id`, `url_hash`) ✅

---

## Schema Applied to code-reviewer.yaml Output

The `prompts/code-reviewer.yaml` template enforces its own output schema inline, demonstrating schema-enforced AI output. The `overall_verdict` enum ensures the model returns only one of three values:

```json
{
  "overall_verdict": "APPROVE_WITH_FIXES",
  "findings": [
    {
      "id": "FIND-001",
      "category": "OWASP_A10_SSRF",
      "severity": "HIGH",
      "description": "UrlValidationError raised inside except ValueError block silently disables SSRF check",
      "location": "validate_url() line 89-98",
      "recommendation": "Use try/except/else pattern",
      "cwe_id": "CWE-754"
    },
    {
      "id": "FIND-002",
      "category": "CODE_QUALITY",
      "severity": "HIGH",
      "description": "Naive/aware datetime comparison crashes expiry check with TypeError",
      "location": "redirect_to_url() line 130",
      "recommendation": "Normalize with .replace(tzinfo=timezone.utc) when tzinfo is None",
      "cwe_id": "CWE-697"
    }
  ],
  "spec_compliance": {
    "compliant_reqs": ["REQ-SHORT-001", "REQ-SHORT-002", "REQ-SHORT-003", "REQ-SHORT-006"],
    "non_compliant_reqs": [
      {"req_id": "REQ-SHORT-004", "reason": "Expiry check crashes before 410 is returned"},
      {"req_id": "REQ-SHORT-005", "reason": "SSRF check silently passes private IPs"}
    ],
    "missing_reqs": []
  },
  "review_id": "REV-001",
  "file_path": "src/utils.py, src/routers/urls.py",
  "checked_at": "2026-05-29T08:00:00Z"
}
```

This output was validated against the `output_schema` in `prompts/code-reviewer.yaml` before being used to drive the fixes in Cycle 1 of the self-critique loop (see `docs/self-critique-log.md`).

---

## How Schema Enforcement Was Applied

1. **API response validation** — Pydantic's `UrlCreateResponse` model validates every `POST /urls` response against the schema at runtime. Any response that doesn't match (e.g., missing `short_code`, wrong `short_code` length) raises a `ValidationError` before the response is sent.

2. **AI output enforcement** — The `output_schema` field in each YAML prompt template constrains the model's output structure. When the `code-reviewer.yaml` prompt was used during the self-critique loop, the response was validated against the schema — `findings[].severity` must be one of `[CRITICAL, HIGH, MEDIUM, LOW, INFO]`, and `overall_verdict` must be one of `[APPROVE, APPROVE_WITH_FIXES, BLOCK]`.

3. **Test assertions** — `test_shorten_url_response_contains_all_required_fields()` in `tests/test_url_shortening.py` verifies the response contains all required schema fields at integration test time.
