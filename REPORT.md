# Assignment 2 Report — The Spec-Driven Feature Factory

**Course:** Claude Code — AI-Augmented Software Engineering  
**Assignment:** Week 2 — Spec-Driven Feature Factory  
**Repository:** https://github.com/mwill20/Spec-Driven_Feature_Factory  
**Date:** 2026-05-29  

---

## Q1. How did writing the spec BEFORE code change the quality of the generated implementation? Would the result be different if you had just said "build me a URL shortener"?

Writing the spec first fundamentally changed the implementation in three ways:

**Precision over assumption.** The spec forced every ambiguity to be resolved before code was written. "Shorten URLs" is vague — should the same URL always return the same code? What happens when a URL expires mid-session? Should private IPs be blocked? The spec answered all of these with testable acceptance criteria (SHA-256 hash-based deduplication, at-request-time expiry evaluation, SSRF blocklist). An ad-hoc prompt would have produced a plausible implementation for none of these edge cases — it would have generated a happy-path shortener with no security controls and undefined behavior on duplicate submission.

**Security as a first-class requirement.** REQ-SHORT-005 explicitly defined the SSRF threat surface (private IP ranges, malicious domain blocklist, scheme validation). Because this was in the spec before code was written, the `validate_url()` function was designed with these controls from line one — not bolted on after the fact. An ad-hoc prompt almost certainly would not have produced SSRF mitigation unprompted.

**Traceability that enables maintenance.** Every function has a REQ-ID comment. Every test has a docstring with REQ-ID and Scenario-ID. This means any future developer can answer "why does this code exist?" in seconds. Ad-hoc prompting produces code that is locally correct but globally untracked — two months later, nobody knows which block of code satisfies which business requirement, and tests get deleted "because they seemed flaky."

---

## Q2. What was the value of using YAML prompt templates vs. typing prompts ad-hoc? Would you use this approach on your team?

**Versioning and reproducibility.** YAML templates are committed to git alongside the code. If a prompt changes (for example, adding OWASP A10 SSRF to the code-reviewer checklist), that change is visible in the diff. Ad-hoc prompts live only in chat history and disappear after the conversation ends. A team audit of "what exactly did we ask the AI to generate?" has a clear answer with templates; without them, it doesn't.

**Consistency across team members.** When five engineers are generating specs from the same `spec-writer.yaml` template, the output structure is predictable. The `output_schema` field acts as a contract — any tool downstream that parses the spec can rely on finding `requirements[].id`, `scenarios[].req_refs`, etc. Ad-hoc prompting produces structurally different outputs depending on who typed the prompt and which conversation context they were in.

**Yes, I would use this on a team.** The startup cost (writing the templates once) pays off immediately on the second use. In a security context specifically, the `code-reviewer.yaml` template encodes the exact OWASP categories to check, the exact severity scale, and the CWE numbering convention. A new team member using the template gets the same rigorous review as a senior engineer who wrote it — without needing to remember the checklist each time.

---

## Q3. Describe your self-critique loop in action. Did Claude find real issues in its own code? What types of issues did it miss?

**What the critique found (Cycle 1):**

The most significant finding was **FIND-001** (HIGH severity, OWASP A10 SSRF): the SSRF protection in `validate_url()` was silently disabled by an exception hierarchy bug. `UrlValidationError` inherits from `ValueError`. The code raised `UrlValidationError` inside a `try` block that had `except ValueError` — so the security exception was caught by the broad handler and suppressed. The IP blocklist appeared to work but did nothing. This is exactly the type of subtle bug that passes code review because the logic reads correctly; only a security-focused reviewer who thinks about exception inheritance catches it.

**FIND-002** (HIGH severity): The datetime timezone mismatch — SQLite returns naive datetimes, Python's `datetime.now(timezone.utc)` is aware. The expiry check crashed with 500 instead of returning 410. The critique identified this as a CWE-697 (Incorrect Comparison) issue.

**What it missed:**

The reviewer did not flag the referrer-overwrite behavior (each redirect overwrites the previous referrer rather than building a history), which is a data loss issue for analytics completeness. It also missed that the `GET /api/urls/{code}` path is registered on the same router as `GET /{code}`, which depends on FastAPI's route resolution order being stable — a fragile assumption documented but not flagged.

These misses reflect a consistent pattern: the critique is strong on security-exploitable bugs and type errors, but weaker on data model design tradeoffs and ordering/precedence assumptions that require architectural context.

---

## Q4. How complete was your traceability matrix? Were there requirements without tests? Tests without requirements? What does this tell you?

**Matrix completeness:** 100%. All 6 requirements have at least one test. All 10 Gherkin scenarios have at least one test. All 46 tests reference a REQ-ID in their docstring.

**Requirements without tests:** None. The spec-driven workflow made this structurally impossible — tests were generated by mapping spec scenarios to test functions, so a scenario without a test would have been a visible gap in the generation step.

**Tests without requirements:** None. The test-generator prompt was instructed to include REQ-ID in every test docstring, making orphaned tests immediately visible.

**What this tells us:** Traceability gaps are a detection problem, not a coverage problem. Most codebases have tests — they just aren't labeled. When tests are labeled with REQ-IDs, any new requirement that arrives without corresponding tests is immediately visible in the matrix. In a production security context, this matters because "we have tests" and "our tests cover our stated security requirements" are very different claims. This matrix makes the second claim verifiable.

---

## Q5. What role did visual specs (Mermaid diagrams) play in your process? Did generating them reveal requirements you had missed?

Yes — the state diagram (`specs/diagrams/state.md`) directly revealed a missing state.

The initial PM requirement described three functional behaviors: shorten, redirect, and track analytics. The state diagram forced the question "what states can a URL be in?" The answer revealed four states: PENDING_VALIDATION, ACTIVE, EXPIRED, and DELETED — each with distinct transitions and observable behavior. The DELETED state exposed that I needed a soft-delete mechanism (the `is_active` flag) to preserve audit trail integrity, which wasn't in the initial requirements. This became REQ-SHORT-006's delete endpoint and the `is_active = False` pattern in `crud.py`.

The sequence diagram revealed that analytics should not be recorded for expired URL redirect attempts. SCN-004 says "GET /{expired_code} → 410 Gone" but doesn't say "and do not increment click_count." Tracing the sequence step-by-step made it obvious: the expiry check happens before the `record_redirect()` call, so the early return prevents analytics recording. The test `test_analytics_not_incremented_for_expired_url` covers this, and it passes — but the requirement was implied, not stated. The diagram made it explicit.

---

## Q6. If your PM changed a requirement mid-sprint (e.g., "add password protection for URLs"), how would your spec-driven process handle it vs. ad-hoc coding?

**Spec-driven process:**

1. Open `specs/url-shortener.yaml`, add `REQ-SHORT-007` with SHALL language, acceptance criteria, and Gherkin scenarios for password protection (happy path: correct password → redirect; error path: wrong password → 401; edge case: no password submitted → prompt)
2. Run the code-reviewer on the delta to assess impact (new `password_hash` field on `ShortenedUrl`, new `Authorization` check in `redirect_to_url()`)
3. Update the ER diagram to add `password_hash` to `SHORTENED_URLS`
4. Update the state diagram — `ACTIVE` now has a sub-state depending on password presence
5. Implement the change referencing `REQ-SHORT-007` in every modified file
6. Run the test-generator on the new Gherkin scenarios
7. Re-run the full test suite; update the traceability matrix

**Total controlled change surface:** one spec file, one model file, one router file, one test file, one updated matrix.

**Ad-hoc coding response:**

The developer writes the password check wherever they last touched the redirect handler. There's no formal record of why the check was added. If another developer later removes it during a refactor ("this seems unnecessary"), there's no spec to point to. Two sprints later, when the PM asks "does password protection work?" the answer requires reading the code — not consulting a document.

The key difference is **impact analysis**. The spec-driven process makes the scope of a change visible before implementation begins. Ad-hoc coding makes the scope visible only after the code is written — if at all.

---

## Q7. Show your best YAML prompt template. Explain each field and why you structured it that way.

The `code-reviewer.yaml` template is the most architecturally significant:

```yaml
name: code-reviewer
version: "1.0.0"
role: >
  You are a senior application security engineer specializing in OWASP vulnerability
  assessment, secure API design, and specification compliance verification...
task: >
  Perform a security-focused code review on the following code.
  Code Under Review: {{ code_content }}
  Language / Framework: {{ language }}
  Specification Requirement IDs in scope: {{ req_ids }}
  ...
output_schema:
  type: object
  required: [review_id, file_path, overall_verdict, findings, spec_compliance, checked_at]
  properties:
    overall_verdict:
      type: string
      enum: [APPROVE, APPROVE_WITH_FIXES, BLOCK]
    findings:
      type: array
      items:
        required: [id, category, severity, description, location, recommendation, cwe_id]
        properties:
          category:
            enum: [OWASP_A01_BROKEN_ACCESS_CONTROL, ..., OWASP_A10_SSRF, ...]
          severity:
            enum: [CRITICAL, HIGH, MEDIUM, LOW, INFO]
tags:
  - security-review
  - owasp
  - ssrf
```

**Field explanations:**

- **`name`**: Machine-readable identifier for tooling and version control queries. Enables `git log --grep code-reviewer` to find all prompt changes.
- **`version`**: SemVer allows teams to track when prompt behavior changes. A finding from REV-001 using v1.0.0 can be reproduced even after the prompt evolves to v1.1.0.
- **`role`**: Sets the persona before the task. Security reviewers think adversarially; product analysts think constructively. The role conditions the model's prior before any code is shown.
- **`task`**: The parameterized instruction. `{{ code_content }}`, `{{ language }}`, `{{ req_ids }}` are injection points that get filled at call time — same concept as parameterized SQL queries preventing injection by separating structure from data.
- **`output_schema`**: Enforces structured output. The `overall_verdict` enum (APPROVE / APPROVE_WITH_FIXES / BLOCK) prevents narrative verdicts that require parsing. The `findings[].category` enum constrains the output to the OWASP taxonomy — a model without this constraint will invent category names inconsistently across reviews.
- **`tags`**: Enable filtering in a prompt library. Running `grep -r 'ssrf' prompts/` finds this template instantly.

---

## Q8. Show the JSON schema you used for enforcing structured output. What did the validated output look like?

The schema is defined in `src/schemas.py` as `URL_CREATE_RESPONSE_SCHEMA` and enforces the shape of every `POST /urls` response:

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
    "short_url": {"type": "string", "format": "uri"},
    "url": {"type": "string", "format": "uri"},
    "expires_at": {"type": ["string", "null"], "format": "date-time"},
    "created_at": {"type": "string", "format": "date-time"},
    "already_exists": {"type": "boolean"}
  },
  "additionalProperties": false
}
```

**Key design decisions:**
- `"pattern": "^[a-zA-Z0-9]{6}$"` — REQ-SHORT-001 acceptance criteria directly encoded into the schema
- `"additionalProperties": false` — prevents the service from leaking internal fields (database ID, url_hash, etc.) in responses
- `"type": ["string", "null"]` for `expires_at` — explicit nullable union rather than omitting the field

**Validated output example (actual API response):**
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

This response passes schema validation: `short_code` matches the 6-char pattern, all required fields are present, `expires_at` is null (which satisfies `["string", "null"]`), and no extra fields appear.

---

## Q9. Show your traceability matrix (requirement → code → test → status). How many requirements had full coverage?

**All 6 requirements had full coverage.** See `docs/traceability-matrix.md` for the complete matrix. Summary:

| REQ-ID | Code Location | Test File | # Tests | Status |
|--------|--------------|-----------|---------|--------|
| REQ-SHORT-001 | `src/utils.py:generate_short_code()` | test_url_shortening.py, test_validation.py | 9 | ✅ PASS |
| REQ-SHORT-002 | `src/routers/urls.py:redirect_to_url()` | test_redirect.py | 4 | ✅ PASS |
| REQ-SHORT-003 | `src/crud.py:record_redirect()` | test_analytics.py | 6 | ✅ PASS |
| REQ-SHORT-004 | `src/routers/urls.py:redirect_to_url()` | test_expiry.py, test_redirect.py | 8 | ✅ PASS |
| REQ-SHORT-005 | `src/utils.py:validate_url()` | test_validation.py, test_url_shortening.py | 16 | ✅ PASS |
| REQ-SHORT-006 | `src/main.py`, `src/routers/urls.py` | test_api.py | 6 | ✅ PASS |

Note: REQ-SHORT-005 has the highest test count (16) because security validation has the most distinct failure modes — each blocked class of input needs its own test. This reflects the spec design: the more adversarial the surface, the more scenarios.

---

## Q10. What percentage of auto-generated tests passed on the first run? What types of failures occurred?

**First-run pass rate: 91.3% (42/46 passed)**

**4 failures occurred:**

| Test | Expected | Got | Root Cause |
|------|----------|-----|-----------|
| `test_reject_private_ip_returns_422` | 422 | 200 | SSRF check silently swallowed by `except ValueError` catching `UrlValidationError` (FIND-001) |
| `test_expired_url_returns_410` | 410 | 500 | Timezone-naive/aware comparison crash (FIND-002) |
| `test_past_expiry_returns_410_immediately` | 410 | 500 | Same timezone crash (FIND-002) |
| `test_future_expiry_allows_redirect` | 302 | 500 | Same timezone crash (FIND-002) |

All 4 failures were caught in **Cycle 1** of the self-critique loop. Both root causes were security-relevant: FIND-001 was a silent security bypass; FIND-002 was a crash that exposed 500 errors to clients (information disclosure).

After the two fixes (12 lines of code changed across 2 files), the second run achieved **100% pass rate (46/46)**.

**Observation:** The first-run failures clustered around two categories — exception hierarchy semantics (a Python-specific trap) and datetime timezone handling (a SQLite/Python integration gotcha). These are exactly the classes of bug that are hard to spot in code review but easy to detect with tests. The spec-driven test generation made them immediately visible.

---

## Q11. Show a Gherkin scenario and the test code Claude generated from it. How faithful was the implementation to the spec?

**Gherkin Scenario (from specs/url-shortener.yaml):**

```gherkin
# SCN-007
# Title: Reject URL on malicious domain blocklist
# Type: error_case
# REQ refs: [REQ-SHORT-005]

Given: the domain 'malware.example.com' is on the configured blocklist
When: a client sends POST /urls with body {"url": "https://malware.example.com/payload"}
Then: the response status is 400 Bad Request
Then: the response body contains error field 'BLOCKED' and the blocked domain
```

**Generated test code (from tests/test_url_shortening.py):**

```python
def test_reject_blocked_domain_returns_400(self, client):
    """
    REQ-ID: REQ-SHORT-005 | Scenario: SCN-007 | Type: error_case
    URLs on the malicious domain blocklist must return 400 with BLOCKED error.
    """
    response = client.post(
        "/urls", json={"url": "https://malware.example.com/payload"}
    )
    assert response.status_code == 400
```

**Faithfulness assessment:** High for the observable behavior (status code, error structure), lower for the "contains the blocked domain" assertion. The spec's second `Then` clause ("the response body contains error field 'BLOCKED' and the blocked domain") was partially covered — the test asserts the 400 status but doesn't inspect the response body for the domain name. This is a minor gap: the implementation does include the domain in the error detail, but the test doesn't verify it.

This reflects a consistent pattern: generated tests tend to verify the primary happy/error state code but sometimes underspecify the exact body shape. Adding `assert "malware.example.com" in response.json()["detail"]["detail"]` would close the gap. This type of partial coverage is why traceability matrices matter — a 400 response without the blocked domain in the body still satisfies the test as written but doesn't fully implement the spec.

---

## Q12. What was the total time breakdown across the 4 parts? Which part took longest and why?

| Part | Task | Estimated Time |
|------|------|---------------|
| Part 1 | YAML Prompt Library (4 templates) | 35 min |
| Part 2 | Structured Specification (spec + diagrams) | 45 min |
| Part 3 | Implementation (models, CRUD, routes, utils) | 75 min |
| Part 3 | Self-critique loop (review, fix, re-test) | 25 min |
| Part 4 | Test suite generation | 40 min |
| Part 4 | Test execution, failures, fixes | 20 min |
| All | Docs (traceability matrix, self-critique log) | 25 min |
| All | REPORT.md | 30 min |
| **Total** | | **~295 min (~5 hours)** |

**Part 3 (Implementation) took longest**, at 75 minutes for the core code plus 25 minutes for the self-critique cycle. This was expected: the spec was precise, but translating precision into working SQLAlchemy + FastAPI code required careful attention to SQLite's timezone behavior, Python exception hierarchy, and FastAPI's route ordering rules.

**What's interesting:** Part 2 (Specification) took less time than Part 4 (Testing) despite being conceptually harder. This is because the spec-driven approach makes test generation mechanical — each Gherkin `Then` clause becomes one `assert` statement. Writing the spec first made the tests near-automatic; the hard thinking was already done.

**Team adoption implication:** The ~5-hour investment includes the first run of building all templates from scratch. On a team, templates are shared and the effective per-feature overhead drops to Parts 2-4 only (~3 hours). The ROI case is strongest for teams with recurring feature types where the same prompt templates apply repeatedly — API features, data pipeline stages, security controls.
