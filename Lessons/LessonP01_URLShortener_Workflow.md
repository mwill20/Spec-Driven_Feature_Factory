# 🎓 Lesson P01: The Approved Change Request — A Claude Code Web Application Build Workflow

## 🛡️ Welcome, Analyst Turning Engineer!

You've submitted a firewall rule change request before. You know the process: document the current state, describe the desired state, define the acceptance criteria, get peer review, test in a lab environment, collect evidence, close the ticket. You've also responded to incidents caused by changes that skipped that process — the rule pushed without peer review, the exception that silently stopped blocking, the rollback plan that existed only in someone's head.

🔍 Today we're exploring **how the URL Shortener Service was actually built** — the real prompts, real YAML templates, and real sequencing that produced `SPEC-SHORT-001 v1.0.0`, a 4-bug self-critique cycle, and 46 passing tests from 42 first-run passes.

> **Companion lesson:** P02 (`LessonP02_URLShortener_Optimal_Workflow.md`) shows what should have happened before Phase 1: a structured `/project-init` interview, an architecture design committed *before* any code, and a `/critique` pass on the spec itself — all before a single source file was created.

---

## 🎯 Learning Objectives

By the end of this lesson you will be able to:

1. Reconstruct the 7-phase workflow used to build the URL Shortener Service from commit history and session artifacts
2. Explain how YAML prompt templates in `prompts/` function as versioned, reusable instruction sets for structured AI output
3. Trace FIND-001 (SSRF bypass) from the self-critique log to the root cause in `src/utils.py` and back to the test that failed because of it
4. Read `docs/traceability-matrix.md` and explain what 100% REQ coverage actually proves — and what it doesn't
5. Identify the two commits that reveal where the actual workflow deviated from the optimal process

**Time estimate:** 50 minutes | **Companion:** `Lessons/LessonP02_URLShortener_Optimal_Workflow.md`

---

## 🧠 What This Lesson Is About — Plain English

This lesson teaches the *workflow* behind the URL Shortener Service — not what the service does architecturally (that's Lessons 01–03), but the sequence of steps used to build it. Understanding the workflow is a different skill from understanding the code: you can read every file in `src/` and still not know whether it was designed first or discovered during implementation.

The workflow that produced this project followed a clear discipline: write the spec before any code, use YAML prompt templates to generate consistent AI output, run the implementation through a structured OWASP security review, and generate tests directly from the spec's Gherkin scenarios. Every deliverable traces back to a document that preceded it.

What makes this workflow worth studying carefully is where it deviated from the optimal path. `docs/ARCHITECTURE.md` and `docs/implementation-plan.md` were not in the initial commit — they appeared in a second commit labeled "delivery audit: add missing required files." The `AGENTS.md` (the document that governs how AI assistants must behave in this repo) was also missing from the initial delivery. These aren't catastrophic failures. They are precisely the kind of process gaps that `/project-init` and `/repo-standards` prevent by design — gaps that are invisible until someone runs an audit.

**Real-world analogy:** The self-critique loop maps directly to a peer review gate on a change ticket. When FIND-001 revealed that the SSRF protection in `validate_url()` was silently disabled by an exception inheritance bug, that's equivalent to discovering during peer review that your new "blocking" correlation rule was set to monitor-only. The code looked correct on inspection. Private IPs appeared to be rejected. Only the adversarial reviewer — thinking about what could go wrong, not what should go right — caught the silent bypass. The 91.3% first-run test pass rate wasn't a failure; it was the detection layer doing exactly what it was designed to do.

---

## 🔵🟡🔴 Career Lens — Three Perspectives on This Workflow

### 🔵 Analyst Lens — What a SOC Analyst Recognizes Here

Every phase in this workflow has a direct parallel to change management processes you already execute:

| SOC / Change Management Task | Claude Code Equivalent |
|-----------------------------|----------------------|
| Write an RFC before touching a firewall rule | `specs/url-shortener.yaml` — formal spec with REQ-IDs before any code |
| Define rollback criteria and acceptance conditions | Each `REQ-SHORT-NNN` acceptance_criteria list: measurable pass/fail |
| Peer review before promoting change to production | `prompts/code-reviewer.yaml` → REV-001 (`APPROVE_WITH_FIXES`) |
| Test change behavior in a lab/staging environment | `pytest tests/ -v` → 42/46 first run: 4 failures exposed FIND-001 & 002 |
| Document evidence trail for ticket closure | `docs/traceability-matrix.md` — REQ → code → test → pass/fail |
| Post-change review noting what was missed | Self-critique log "What the Reviewer Missed" section |

The traceability matrix serves the same function as a change management closure checklist: it proves every stated requirement was implemented *and* tested before the ticket is closed. Without it, the answer to "did we implement what we promised?" requires reading source code instead of consulting a document.

**SOC parallel:** Running `code-reviewer.yaml` on implementation files before committing is the same as submitting a new FortiSIEM correlation rule to peer review before it activates — you are not pushing unreviewed security logic to production.

### 🟡 Engineer Lens — What a Cybersecurity Engineer Builds Here

The most important engineering concept in this workflow is how YAML prompt templates separate **instruction structure** from **input data** — the same principle as parameterized SQL queries separating query structure from user-supplied values.

In `prompts/spec-writer.yaml`:
```yaml
task: >
  Convert the following feature request into a complete formal specification.
  Feature Request: {{ feature_request }}
  System Name: {{ system_name }}
  Requirement ID Prefix: {{ req_prefix }}
  Minimum Gherkin Scenarios: {{ min_scenarios }}
```

The `{{ feature_request }}` is the parameterized input. The rest of the YAML is fixed instruction structure. This means: the template can be audited independently of any specific feature request it processes. Version `1.0.0` of the spec-writer template is a contract; changes to prompt behavior require a version bump and produce a git diff — exactly like a schema migration.

The `output_schema` field in `code-reviewer.yaml` is equally significant. The `overall_verdict` enum (`APPROVE / APPROVE_WITH_FIXES / BLOCK`) prevents the model from producing a narrative verdict that requires human parsing to interpret. The `findings[].category` enum constrains output to the OWASP Top 10 taxonomy — the model cannot invent a category name that doesn't appear in the schema. This is the same principle as an allowlist: define the valid output space and reject everything outside it.

**Engineering decision to own:** The CRUD boundary rule in `AGENTS.md` ("database queries belong ONLY in `src/crud.py`") is an architectural isolation principle. Routers call named CRUD functions; they never write raw ORM queries. This means changing database logic requires touching exactly one file — `src/crud.py` — and the test suite for that file covers all data access behavior. The HTTP layer (`src/routers/urls.py`) cannot drift into accumulating ad-hoc queries, which is how "just one quick db lookup in the router" becomes an unmaintainable persistence layer scattered across every handler.

### 🔴 AI Security Engineer Lens — What an AI/ML Security Engineer Watches For

This project uses AI at two stages: generating implementation code from specs, and reviewing AI-generated code with an AI reviewer. That second pattern — AI reviewing AI — creates a risk that the self-critique log documents honestly in "What the Reviewer Missed":

> "The reviewer did not flag the referrer-overwrite behavior... It also missed that `GET /api/urls/{code}` depends on FastAPI's route resolution order being stable — a fragile assumption documented but not flagged."

When code generator and code reviewer share a training distribution, they tend to share blind spots. A pattern the generator confidently produced is one the reviewer is likely to consider unremarkable. This isn't a flaw specific to this project — it's a structural property of AI-reviewing-AI architectures that requires human supplementation on HIGH severity findings.

The `additionalProperties: false` constraint in `src/schemas.py`'s `URL_CREATE_RESPONSE_SCHEMA` addresses a different AI security surface: it ensures no internal field (`id`, `url_hash`, or any field a future model-generated refactor might introduce) can appear in an API response. This is output sanitization for AI-assisted development — a guardrail that doesn't require the model to "know" about field sensitivity; the schema enforces it structurally.

**AI security surface:** The `output_schema` enums in `code-reviewer.yaml` mitigate a specific prompt injection risk against the review pipeline. If malicious content were injected into code comments (indirect prompt injection), the attacker cannot change the review verdict to `APPROVE` through natural language manipulation alone — the `overall_verdict` field is constrained to a closed three-value enum, not a free-text field.

---

## 🗺️ The 7-Phase Build Workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PHASE 1       │    │   PHASE 2       │    │   PHASE 3       │
│  SPEC WRITING   │───▶│ DIAGRAM DESIGN  │───▶│ PROMPT LIBRARY  │
│                 │    │                 │    │                 │
│ spec-writer.yaml│    │ Mermaid (state, │    │ 4 YAML templates│
│ → SPEC-SHORT-001│    │  seq, ER)       │    │ versioned in    │
│ 6 REQs, 10 SCNs │    │ → revealed DELETED    │ prompts/        │
└─────────────────┘    │   state gap     │    └─────────────────┘
                       └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PHASE 6       │    │   PHASE 5       │    │   PHASE 4       │
│ TEST GENERATION │◀───│ SELF-CRITIQUE   │◀───│ IMPLEMENTATION  │
│   & EXECUTION   │    │    LOOP         │    │                 │
│                 │    │                 │    │ src/ with       │
│ test-generator  │    │ code-reviewer   │    │ REQ-ID comments │
│ → 46 tests      │    │ → REV-001 FIXES │    │ 6 modules built │
│ 42/46 first run │    │ → REV-002 APPR. │    │                 │
│ 46/46 post-fix  │    │ FIND-001, -002  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   PHASE 7       │
│  DOCUMENTATION  │
│ & KNOWLEDGE     │
│   CAPTURE       │
│                 │
│ traceability-   │
│ matrix, REPORT, │
│ Lessons 01-03   │
│                 │
│ [AUDIT CATCH:   │
│  ARCHITECTURE,  │
│  AGENTS.md,     │
│  impl-plan →    │
│  commit 2]      │
└─────────────────┘
```

---

## 🔑 Key Concepts

### 1. REQ-ID Traceability

Every requirement in `specs/url-shortener.yaml` has a unique identifier (`REQ-SHORT-NNN`). Every source file in `src/` has a comment citing the REQ-IDs it implements. Every test function in `tests/` has a docstring format:

```python
"""
REQ-ID: REQ-SHORT-005 | Scenario: SCN-010 | Type: error_case
POST /urls with private IP must return 422 (SSRF prevention).
"""
```

**Security implication:** When a security control is removed or modified during a refactor, the REQ-ID comment triggers the question: "does this change still satisfy REQ-SHORT-005?" — the same way a change request forces the question "does this modification still satisfy the approved use case?" Without REQ-IDs, controls are removed by developers who don't realize what they're deleting. The identifier is the link between *what the code does* and *why it must exist*.

### 2. The Generate → Review → Fix Cycle

The self-critique loop applies `code-reviewer.yaml` to implementation code, produces structured findings (FIND-NNN) with OWASP category and CWE number, applies fixes, then runs the reviewer again. The loop terminates at `APPROVE`.

**Security implication:** This is threat validation in development, not production. FIND-001 (SSRF bypass via exception inheritance) and FIND-002 (datetime crash producing 500 instead of 410) were both caught before any real user could trigger them. The 8.7% first-run test failure rate was the detection layer working exactly as designed — not a quality failure.

### 3. Schema-Enforced Output Boundaries

`src/schemas.py` defines `URL_CREATE_RESPONSE_SCHEMA` as a JSON Schema with `"additionalProperties": false`. The `short_code` pattern `"^[a-zA-Z0-9]{6}$"` encodes REQ-SHORT-001's 6-character acceptance criterion directly into the validation layer. Every `POST /urls` response is validated before returning.

**Security implication:** Schema enforcement prevents data leakage. Even if a future AI-assisted refactor adds an `id` or `url_hash` field to an internal response model, `additionalProperties: false` ensures it never reaches the API consumer. The spec's data model section lists both fields as internal-only — the JSON Schema enforces that contract at runtime, regardless of what the code generates.

---

## 📝 Phase-by-Phase Walkthrough

### Phase 1: Spec Writing

The specification was generated using `prompts/spec-writer.yaml` applied to the PM feature request: "Build a URL shortener that shortens URLs, redirects users, and tracks click analytics."

The template's parameterized injection points:
```yaml
Feature Request: {{ feature_request }}
System Name: {{ system_name }}
Requirement ID Prefix: {{ req_prefix }}
Minimum Gherkin Scenarios: {{ min_scenarios }}
```

Output: `specs/url-shortener.yaml` (SPEC-SHORT-001 v1.0.0) — 6 functional requirements, 4 non-functional requirement groups, 10 Gherkin scenarios, a full OpenAPI 3.0-style API contract, and a data model.

Key spec decisions forced by the format: REQ-SHORT-005 explicitly named SSRF threat surfaces (private IP ranges, domain blocklist, scheme validation) as MUST requirements with measurable acceptance criteria. From REPORT.md Q1: "An ad-hoc prompt almost certainly would not have produced SSRF mitigation unprompted."

> **Pitfall:** The spec was written from a feature request alone, with no structured interview phase first. The SSRF threat surface made it into REQ-SHORT-005 because the spec author knew to include it — not because a structured interview surfaced it. A different author, or a simpler feature request, might have produced a spec with no security NFRs at all. P02, Phase 1 shows how `/project-init` prevents this.

---

### Phase 2: Diagram Design

Three Mermaid diagrams were generated alongside the spec:

- `specs/diagrams/er.md` — Entity-Relationship model of `shortened_urls` and `blocklist` tables
- `specs/diagrams/sequence.md` — URL shortening and redirect flow sequences
- `specs/diagrams/state.md` — URL lifecycle: PENDING_VALIDATION → ACTIVE → EXPIRED / DELETED

From REPORT.md Q5: "The state diagram forced the question 'what states can a URL be in?' The answer revealed four states... The DELETED state exposed that I needed a soft-delete mechanism (`is_active` flag)... This became REQ-SHORT-006's delete endpoint."

This is design discovery: the diagram surfaced a requirement the feature request hadn't stated. The sequence diagram revealed an implied (but unwritten) requirement — that analytics should not increment for expired URL redirect attempts. The test `test_analytics_not_incremented_for_expired_url` covers it, and it passes — but the requirement is implied, not stated in the spec.

> **Pitfall:** An implied requirement is still a spec gap. The test passes because the implementation handles it correctly, but there is no `REQ-SHORT-NNN` entry that says "analytics MUST NOT increment for expired redirects." Two months from now, a developer refactoring `redirect_to_url()` won't know this constraint exists unless they read the test. Document implications as requirements.

---

### Phase 3: Prompt Library Build

Four YAML prompt templates were committed to `prompts/`:

| Template | Role | Key Output Constraint |
|----------|------|----------------------|
| `spec-writer.yaml v1.0.0` | Product analyst | `requirements[].id` follows `REQ-{PREFIX}-NNN` |
| `architect.yaml v1.0.0` | Implementation planner | Numbered tasks with REQ refs and acceptance criteria |
| `code-reviewer.yaml v1.0.0` | OWASP security reviewer | `overall_verdict` enum: APPROVE / APPROVE_WITH_FIXES / BLOCK |
| `test-generator.yaml v1.0.0` | Test author | Every test function must include REQ-ID in docstring |

Each template includes a `version` field and `tags` for searchability. The `code-reviewer.yaml` encodes the full OWASP Top 10 taxonomy as an enum on `findings[].category` — the reviewer cannot invent a non-OWASP finding category, which means outputs are parseable by tooling without string manipulation.

> **Pitfall:** Templates are only as enforceable as their `output_schema` fields. A template without a schema produces consistent-looking but structurally variable output across different invocations — equivalent to a SIEM rule that generates alerts with inconsistent field names. If `test-generator.yaml` doesn't require the REQ-ID docstring, generated tests will not be traceable even if they pass.

---

### Phase 4: Implementation

Six source files were built in `src/`, each with REQ-ID comment headers:

| File | Core Responsibility | Security Mechanism |
|------|--------------------|--------------------|
| `src/utils.py` | URL validation, SSRF prevention, code generation | `try/except/else` exception isolation, CSPRNG via `SystemRandom()` |
| `src/models.py` | SQLAlchemy ORM models | `url_hash` UNIQUE constraint; `is_active` soft-delete |
| `src/schemas.py` | Pydantic request/response + JSON Schema | `additionalProperties: false`; `short_code` pattern enforcement |
| `src/crud.py` | All database operations | Hash-based dedup; soft delete; blocklist load |
| `src/routers/urls.py` | HTTP route handlers | At-request-time expiry; explicit datetime normalization |
| `src/main.py` | App entry, lifespan, error handlers | Structured error responses; no stack trace leakage |

AGENTS.md mandates that routers never write raw ORM queries (`db.query()` belongs only in `src/crud.py`). This is a layer isolation rule — analogous to separating log parsing from correlation logic in a SIEM: each layer does one thing.

> **Pitfall:** Two bugs were introduced during implementation that were not visible from code inspection: (1) the SSRF check was silently disabled by exception inheritance (FIND-001), and (2) timezone-naive datetime comparison crashed with 500 instead of 410 (FIND-002). Both required either adversarial review or test execution to surface. Code reading is not sufficient for security validation.

---

### Phase 5: Self-Critique Loop

`prompts/code-reviewer.yaml` was applied to `src/utils.py`, `src/routers/urls.py`, and `src/crud.py`. REV-001 findings:

| ID | Severity | OWASP Category | Root Cause | Fix |
|----|----------|----------------|-----------|-----|
| FIND-001 | HIGH | OWASP_A10_SSRF | `UrlValidationError(ValueError)` raised inside `except ValueError` — security exception silently caught and suppressed. CWE-754. | Changed to `try/except/else` — exception handler only catches IP parsing failures, not our own validation exceptions. |
| FIND-002 | HIGH | CODE_QUALITY | SQLite returns naive `datetime` objects; `datetime.now(timezone.utc)` is timezone-aware. Comparison raises `TypeError` → 500 instead of 410. CWE-697. | Added `.replace(tzinfo=timezone.utc)` normalization when `expires_at.tzinfo is None`. |
| FIND-003 | MEDIUM | OWASP_A09_LOGGING | Blocked domain logged at WARNING but domain name omitted — forensic reconstruction incomplete. | Added `exc.error_code` to log message. |
| FIND-004 | LOW | SPEC_COMPLIANCE | Route ordering: `/api/urls/{code}` and `/{code}` on same router — ordering dependency. | Verified FastAPI registration order; no conflict. No fix. |

Verdict: `APPROVE_WITH_FIXES`. After applying FIND-001 and FIND-002 fixes (12 lines across 2 files), REV-002 verdict: `APPROVE`.

> **Pitfall:** The reviewer missed referrer-overwrite data loss (each redirect overwrites the previous referrer rather than building history), URL redirect chaining (submitting `https://bit.ly/x` bypasses single-level SSRF), and the route resolution ordering fragility. These are documented honestly in the "What the Reviewer Missed" section. An incomplete review that pretends completeness is worse than an honest review that documents gaps — future developers inherit false confidence.

---

### Phase 6: Test Generation & Execution

`prompts/test-generator.yaml` was applied to the 10 Gherkin scenarios in `specs/url-shortener.yaml`. Output: 46 test functions across 6 test files, each with a REQ-ID docstring.

**First-run results:**
```
46 collected
42 passed / 4 failed  (91.3% first-run pass rate)
```

| Failing Test | Expected | Got | Finding |
|-------------|----------|-----|---------|
| `test_reject_private_ip_returns_422` | 422 | 200 | FIND-001: SSRF check silently bypassed |
| `test_expired_url_returns_410` | 410 | 500 | FIND-002: datetime comparison crash |
| `test_past_expiry_returns_410_immediately` | 410 | 500 | FIND-002 |
| `test_future_expiry_allows_redirect` | 302 | 500 | FIND-002 |

After applying FIND-001 and FIND-002 fixes: **46/46 passed (100%)**.

The test failures clustered around exactly the two HIGH severity findings the code reviewer identified. This is the system working correctly: tests don't just verify features, they verify security controls.

> **Pitfall:** A test that only checks the HTTP status code partially covers a Gherkin scenario. `test_reject_blocked_domain_returns_400` asserts `response.status_code == 400` but doesn't verify `"malware.example.com"` appears in the error detail — which is the second `Then` clause of SCN-007. The implementation includes the domain in the detail; the test doesn't verify it. This is a traceability gap: coverage at the status-code level, incomplete coverage at the response-body level.

---

### Phase 7: Documentation & Knowledge Capture

Three documentation artifacts were produced post-implementation:

1. **`docs/traceability-matrix.md`** — maps all 6 REQ-IDs to code locations, test files, and individual test functions; confirms 6/6 requirements fully covered, 0 orphaned tests
2. **`docs/self-critique-log.md`** — records both review cycles, all 4 findings with severity/CWE, fixes applied, and accepted residual risks
3. **`REPORT.md`** — written answers to 12 assignment questions serving as retrospective and institutional knowledge transfer

Content lessons (`Lessons/Lesson01–03`) were generated using `/lesson-gen` to teach the spec, data layer, and SSRF validation components.

**The delivery audit gap:** `docs/ARCHITECTURE.md`, `docs/implementation-plan.md`, `AGENTS.md`, `.env.example`, and `docs/LIMITATIONS.md` were all absent from the initial commit and added only after a post-delivery audit. The architecture and implementation plan had been generated using `prompts/architect.yaml` during the session, but were not committed as part of the primary delivery. Notably, `docs/implementation-plan.md` explicitly lists "Private IP check uses `try/except/else` to prevent exception inheritance bypass" as a TASK-002 acceptance criterion — but the code initially didn't implement this, and FIND-001 caught it. This means the implementation plan, as committed, reflects the post-fix state of the code: it is documentation of what was built, not a design constraint that drove the build.

> **Pitfall:** Architecture documentation written after the code is an accurate description of the system, not a design that shaped it. The distinction matters: when ARCHITECTURE.md describes the CRUD boundary rule, it's documenting a pattern that already exists. When it's written *before* code, it's a constraint the implementation must satisfy. P02, Phase 3 shows how `/architect` changes this.

---

## 🧪 Hands-On Exercises

### Exercise 1: Run the Validation Command and Read a REQ-ID Docstring

**Goal:** Confirm 46 tests pass and trace a specific test back to its spec requirement.

```powershell
.\.venv\Scripts\python -m pytest tests/test_validation.py -v
```

**Expected output:** `16 passed` — all REQ-SHORT-005 validation tests passing.

**Success criterion:** Open `tests/test_validation.py`, find `test_reject_private_ip_returns_422`, and read its docstring. Confirm it contains `REQ-ID: REQ-SHORT-005 | Scenario: SCN-010 | Type: error_case`. This is the test that returned `200` instead of `422` on first run — evidence that FIND-001 disabled the SSRF check.

---

### Exercise 2: Trace FIND-001 from Discovery to Fix

**Goal:** Follow the exception inheritance bug from review finding to patched code.

1. Open `docs/self-critique-log.md` — read FIND-001's description and the "Fix Applied" column
2. Open `src/utils.py` — find `validate_url()` and locate the `try/except/else` block
3. Read the comment in `utils.py` explaining why `except ValueError` could not catch `UrlValidationError`

**Success criterion:** Explain in one sentence why `UrlValidationError(ValueError)` raised inside `except ValueError` silently disabled the SSRF check — and how `try/except/else` prevents this.

---

### Exercise 3: Read Spec to Acceptance Criteria to Test to Assertion

**Goal:** Trace a complete path: spec requirement → Gherkin scenario → test function → assert statement.

1. Open `specs/url-shortener.yaml` — find `REQ-SHORT-004` and read its `acceptance_criteria`
2. Find `SCN-004` in the scenarios section — read the `then` clauses
3. Run: `.\.venv\Scripts\python -m pytest tests/test_expiry.py -v`
4. Open `tests/test_expiry.py` — find `test_expired_url_returns_410` and read its assert statement

**Expected output:** `5 passed`.

**Success criterion:** Map the spec's `then: "response status is 410 Gone"` to `assert response.status_code == 410` in the test, and explain why FIND-002 caused this test to return `500` on first run (SQLite's naive datetime could not be compared to `datetime.now(timezone.utc)`).

---

### Exercise 4: Verify Schema Enforcement Prevents Internal Field Leakage

**Goal:** Understand why `additionalProperties: false` is a security control, not just a type check.

1. Open `src/schemas.py` — find `URL_CREATE_RESPONSE_SCHEMA` and its `required` field list
2. Note that `id` and `url_hash` are NOT in the `required` list and are not defined as `properties`
3. Open `specs/url-shortener.yaml` — find the `data_model` section. Confirm `id` and `url_hash` appear in the `ShortenedUrl` entity fields but NOT in the API contract response schema (Section 4)

**Success criterion:** Explain why `additionalProperties: false` means a future refactor that accidentally adds `url_hash` to the Pydantic response model will be caught at test time (the schema validation will fail), not at production runtime.

---

## 📚 Interview Preparation

### 🟡 Cybersecurity Engineering Interview

**Q: You ran a self-critique loop on this project and found that SSRF protection was silently disabled. How did that happen, and what does it tell you about validating security controls in code?**

**A:** `UrlValidationError` inherits from `ValueError`. The SSRF check raised `UrlValidationError` inside a `try` block that also had an `except ValueError` handler — intended to catch failures from Python's `ipaddress` module during IP parsing. Because `UrlValidationError` is a subclass of `ValueError`, the broad exception handler caught the SSRF validation exception and suppressed it before it could propagate to the caller. The IP blocklist appeared to function; the code read correctly; the tests hadn't run yet. The fix was restructuring to `try/except/else`: the `except` clause handles IP parsing errors only; the `else` clause executes the SSRF check in a scope where `except ValueError` cannot intercept it.

The broader lesson: security controls that involve exception handling require explicit verification that the exception flow behaves as intended. Reading code is not sufficient — FIND-001 was invisible to code review. Running the test `test_reject_private_ip_returns_422` and seeing `200` instead of `422` made the bug undeniable.

### 🔴 AI Security Engineering Interview

**Q: This project uses AI to generate code and then uses a different AI prompt to review that code. What specific risk does that create, and what controls would you add in a production security context?**

**A:** When code generator and code reviewer are trained on similar distributions, they share blind spots. The generator produces patterns it's confident about; the reviewer evaluates those same patterns as familiar and unremarkable. This is exactly what the self-critique log documents: the reviewer missed referrer-overwrite data loss, URL redirect chaining, and route resolution ordering fragility — all subtle, context-dependent issues that require architectural understanding, not just pattern matching.

In production, I'd add three controls: (1) Use a reviewer with explicitly different fine-tuning or a different base model than the generator; (2) supplement AI review with deterministic SAST (Bandit for Python, Semgrep rules for OWASP SSRF patterns) that doesn't share the model's blind spots; (3) require human sign-off on any HIGH or CRITICAL severity finding regardless of the AI verdict — the AI can identify and classify, but a human confirms that the proposed fix actually closes the gap. In this project, FIND-001's fix was correct, but a human reviewer would also verify the fix didn't introduce a new exception handling pattern that bypassed something else.

---

## ✅ Key Takeaways

1. **The spec is the change ticket.** Every `REQ-SHORT-NNN` served the same function as a formal change request: stated desired behavior, defined measurable acceptance criteria, and became the traceable record explaining why the code exists.

2. **YAML prompt templates version your AI instructions alongside your code.** `prompts/code-reviewer.yaml v1.0.0` is as auditable as any git-committed file — you can see exactly what security checklist was active when REV-001 was generated, and track changes to that checklist the same way you track changes to the code it reviews.

3. **91.3% first-run pass rate was a success signal, not a failure.** The 4 failing tests caught two production-level security bugs before any user encountered them. Tests that fail on first run are doing exactly their job; tests that never fail may not be testing the adversarial paths.

4. **Architecture written after code is documentation, not design.** `docs/ARCHITECTURE.md` and `docs/implementation-plan.md` were both committed in the delivery audit pass (commit 2), not in the initial build. They accurately describe the system — but they did not drive it. P02 shows what changes when architecture is designed and committed before implementation begins.

5. **Document what the reviewer missed.** The self-critique log's "What the Reviewer Missed" section distinguishes a real security review from a rubber stamp. Honest gap documentation is what a future maintainer or incident responder needs to know — not just what was found, but what the review process structurally cannot see.

---

## 📋 Quick Reference Card

| Phase | Primary Tool | Command / Template | What It Produced |
|-------|-------------|-------------------|-----------------|
| 1: Spec Writing | `spec-writer.yaml` | `{{ feature_request }}` injection | `specs/url-shortener.yaml` (SPEC-SHORT-001 v1.0.0) |
| 2: Diagram Design | Mermaid | Spec-driven state/sequence/ER diagrams | `specs/diagrams/` (er.md, sequence.md, state.md) |
| 3: Prompt Library | YAML + git | 4 versioned template files | `prompts/*.yaml` (spec-writer, architect, code-reviewer, test-generator) |
| 4: Implementation | `/principal-engineer` | Code against REQ-ID comments | `src/` — 6 modules + router |
| 5: Self-Critique | `code-reviewer.yaml` | `{{ code_content }}` injection | `docs/self-critique-log.md` — FIND-001 through 004 |
| 6: Test Generation | `test-generator.yaml` | `{{ gherkin_scenarios }}` injection | `tests/` — 46 tests, 46/46 pass post-fix |
| 7: Documentation | `/lesson-gen` | Codebase source files | Lessons 01–03, traceability matrix, REPORT.md |

---

## 🚀 Ready for Lesson P02?

Lesson P02 reveals two specific moments where the actual workflow produced avoidable technical debt: the architecture document that was written *after* the code (not before it), and the `AGENTS.md` and `.env.example` that appeared only in commit 2 after a delivery audit — artifacts that `/project-init` and `/repo-standards` generate at project start, before a single line of implementation is written.
