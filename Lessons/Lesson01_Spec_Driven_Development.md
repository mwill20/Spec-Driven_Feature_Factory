# 🎓 Lesson 01: The Blueprint Before the Build — Spec-Driven Development with YAML

## 🛡️ Welcome Back, Security Analyst!

Have you ever triaged an alert and thought: "I wish whoever built this system had documented what it's *supposed* to do"? 🔍 Today we're exploring **Spec-Driven Development** (`specs/url-shortener.yaml` + `prompts/`) — the "incident runbook before the incident" approach that ensures every line of code answers to a documented requirement.

---

## 🎯 Learning Objectives

By the end of this lesson you will be able to:

- Explain why formal specifications reduce security gaps compared to ad-hoc development
- Read and interpret a YAML specification using SHALL/MUST normative language
- Identify how Gherkin scenarios map to test functions and security controls
- Describe how YAML prompt templates enforce consistent AI-generated output structure
- Trace any piece of code back to the requirement that justifies its existence

**Time estimate:** 45 minutes | **Prerequisites:** None

---

## 🧠 What This Component Does — Plain English

Spec-driven development means writing a formal document that describes **exactly what the system must do** before a single line of implementation is written. Think of it as the difference between a SOAR playbook and ad-hoc incident response: the playbook defines the expected behavior, the required steps, and the exit criteria before any alert fires. Without it, every analyst responds differently; with it, the process is repeatable and auditable.

In this project, the specification lives in `specs/url-shortener.yaml`. It defines six requirements (REQ-SHORT-001 through REQ-SHORT-006), ten Gherkin behavioral scenarios, a full API contract with request/response schemas, and non-functional requirements for performance, security, and rate limiting. Every file in `src/` and every test in `tests/` was written *after* this spec existed — and every one of them references the REQ-IDs from the spec.

The `prompts/` directory takes this further: it stores the instructions given to the AI model in versioned YAML files. Just as a SOC stores correlation rules in version-controlled files (not in someone's head), YAML prompt templates store the "how to generate a spec" and "how to review code for OWASP issues" instructions in a form that can be audited, diffed, and shared across a team.

**Real-world analogy:** Your FortiSIEM correlation rules are specifications. They say "IF event type = login_failure AND count > 5 in 60 seconds THEN alert." The rule *precedes* the action — it defines the trigger, the condition, and the expected outcome before a single packet arrives. Spec-driven development applies that same discipline to software: define the trigger (user submits a URL), the condition (it must be valid HTTPS, not private IP, not blocklisted), and the expected outcome (201 with a 6-char code) before writing the function.

---

## 🗺️ Where This Fits in the System

```
📋 PM Feature Request
        ↓
🔍 spec-writer.yaml prompt → specs/url-shortener.yaml (THIS LESSON)
        ↓
🧠 architect.yaml prompt → Implementation plan (task breakdown)
        ↓
💻 src/ — Code written against REQ-IDs
        ↓
🧪 test-generator.yaml prompt → tests/ (one test per Gherkin scenario)
        ↓
✅ Traceability matrix: REQ → code → test → pass/fail
```

If the spec is skipped, the code exists but there is no way to verify whether it satisfies any stated business requirement. You can't answer "does this code implement what we promised?" without the spec.

---

## 🔑 Key Concepts

### Normative Language (SHALL / MUST / SHOULD / MAY)

RFC 2119 defines a vocabulary for writing unambiguous technical requirements. In this project:

- **MUST / SHALL** — non-negotiable. If the code doesn't do this, the requirement is violated. Example: `REQ-SHORT-001` uses MUST — the code *must* return a 6-char code, not a 5-char or 7-char one.
- **SHOULD** — recommended but not absolute. `REQ-SHORT-003` uses SHALL for analytics tracking — strong but allows exceptions in degraded scenarios.
- **MAY** — optional capability the system *can* support.

This vocabulary exists because plain English requirements like "generate a short code" are ambiguous. How short? What characters? Unique across all users or per-session? SHALL/MUST forces the writer to resolve every ambiguity before the reader encounters it.

### Gherkin (Given / When / Then)

Gherkin is a structured format for describing system behavior from the user's perspective. Each scenario answers: what state does the system start in (Given), what action does the user take (When), and what is the observable outcome (Then)?

```gherkin
Given: the domain 'malware.example.com' is on the configured blocklist
When:  a client sends POST /urls with body {"url": "https://malware.example.com/payload"}
Then:  the response status is 400 Bad Request
Then:  the response body contains error field 'BLOCKED' and the blocked domain
```

Each `Then` clause becomes one `assert` statement in a test. If you can't write a `Then` clause for a behavior, the behavior is undefined — which means it either won't be tested or won't be implemented correctly.

### YAML Prompt Templates

A YAML prompt template stores a parameterized AI instruction as a versioned document:

```yaml
name: code-reviewer
version: "1.0.0"
role: >
  You are a senior application security engineer...
task: >
  Review the following code: {{ code_content }}
  Language: {{ language }}
output_schema:
  type: object
  required: [overall_verdict, findings]
  properties:
    overall_verdict:
      enum: [APPROVE, APPROVE_WITH_FIXES, BLOCK]
```

The `{{ variable }}` placeholders are filled at call time — exactly like parameterized SQL queries. The `output_schema` field tells the model what JSON shape to return, which enables downstream schema validation. A model responding to a prompt without a schema constraint might call the severity "serious" in one review and "important" in another — with the schema, both are rejected in favor of the enum `[CRITICAL, HIGH, MEDIUM, LOW, INFO]`.

### Requirement ID Traceability

Every requirement gets a unique ID: `REQ-SHORT-001` through `REQ-SHORT-006`. Every source file that implements a requirement starts with a comment citing those IDs. Every test function has a docstring with the REQ-ID and Gherkin scenario ID. This creates a three-way link: spec → code → test. Any future developer can answer "why does this code exist?" and "is this code tested?" without reading the full codebase.

---

## 📝 Code Walkthrough

### The Spec Structure — Requirements Section

```yaml
# specs/url-shortener.yaml — Lines 28–55 (requirements section)
requirements:

  - id: REQ-SHORT-001
    priority: MUST
    statement: >
      The system MUST accept a valid HTTP or HTTPS URL and return a unique
      alphanumeric short code of exactly 6 characters.
    rationale: Core value proposition of the service.
    acceptance_criteria:
      - "POST /urls with a valid URL body returns HTTP 201 with a `short_code` field"
      - "The returned short_code is exactly 6 characters [a-zA-Z0-9]"
      - "Two distinct valid URLs produce two distinct short codes"
      - "The same URL submitted twice returns the same short code (idempotent)"
```

**Line-by-line breakdown:**

| Field | What it does | Why it was designed this way |
|-------|-------------|------------------------------|
| `id` | Unique identifier in format REQ-{PREFIX}-NNN | Enables grep-based traceability across all project files |
| `priority: MUST` | RFC 2119 normative level | Distinguishes non-negotiable features from optional ones |
| `statement` | Single, unambiguous requirement text | Eliminates "I thought it meant..." disagreements |
| `rationale` | Why this requirement exists | Helps future developers understand if a requirement is still relevant |
| `acceptance_criteria` | Measurable, pass/fail verifiable conditions | Each criterion becomes one or more test assertions |

**Design pattern:** Each acceptance criterion is written as an observable, testable outcome ("returns HTTP 201") not an implementation instruction ("call the database"). This separation means the spec remains valid even if the implementation changes from SQLite to PostgreSQL.

### The Spec Structure — Gherkin Scenarios Section

```yaml
# specs/url-shortener.yaml — Scenario SCN-007
  - id: SCN-007
    title: Reject URL on malicious domain blocklist
    type: error_case
    req_refs: [REQ-SHORT-005]
    given:
      - "the domain 'malware.example.com' is on the configured blocklist"
    when:
      - "a client sends POST /urls with body {\"url\": \"https://malware.example.com/payload\"}"
    then:
      - "the response status is 400 Bad Request"
      - "the response body contains error field 'BLOCKED' and the blocked domain"
```

**Why this structure works:**

The `type` field (`happy_path`, `error_case`, `edge_case`) categorizes scenarios so a reviewer can quickly check "do we have error coverage?" without reading every scenario. The `req_refs` field links the scenario back to the formal requirement it tests — if REQ-SHORT-005 changes, you know SCN-007 needs to change too.

Notice the scenario says nothing about *how* the blocklist is implemented (database table, config file, environment variable). That's intentional: the spec defines observable behavior, not implementation. The test that implements this scenario (`test_reject_blocked_domain_returns_400`) is equally implementation-agnostic.

### The Prompt Template — Output Schema

```yaml
# prompts/code-reviewer.yaml — output_schema section
output_schema:
  type: object
  required:
    - review_id
    - file_path
    - overall_verdict
    - findings
    - spec_compliance
    - checked_at
  properties:
    overall_verdict:
      type: string
      enum: [APPROVE, APPROVE_WITH_FIXES, BLOCK]
    findings:
      type: array
      items:
        type: object
        required: [id, category, severity, description, location, recommendation, cwe_id]
        properties:
          category:
            type: string
            enum:
              - OWASP_A01_BROKEN_ACCESS_CONTROL
              - OWASP_A03_INJECTION
              - OWASP_A10_SSRF
              # ... full OWASP Top 10
          severity:
            type: string
            enum: [CRITICAL, HIGH, MEDIUM, LOW, INFO]
```

> ⚠️ **Common pitfall:** Teams often skip the `output_schema` field, treating prompt templates as just "system prompts." Without schema enforcement, the AI response structure varies per conversation — which means any downstream tool that parses the review JSON breaks unpredictably. With `output_schema`, you can validate the response against the schema before trusting its content, exactly like validating an API response before acting on it.

---

## 🧪 Hands-On Exercises

> Before starting: from the project root, activate the virtual environment.
> ```powershell
> .\.venv\Scripts\Activate.ps1
> ```

### 🔬 Exercise 1: Read the Spec and Find a Requirement

This exercise proves that spec traceability works — you can find any requirement's implementation in under 60 seconds.

```powershell
# Find all files that reference REQ-SHORT-005
Get-ChildItem -Recurse -Include "*.py","*.yaml","*.md" -Path . | 
  Select-String "REQ-SHORT-005" | 
  Select-Object Path, LineNumber, Line
```

📊 **Expected output:**
```
Path                              LineNumber  Line
----                              ----------  ----
.\docs\self-critique-log.md       27          | REQ-SHORT-005 | ⚠️ FIND-001 breaks...
.\docs\traceability-matrix.md     11          | REQ-SHORT-005 | ...
.\specs\url-shortener.yaml        82          - id: REQ-SHORT-005
.\src\crud.py                     1           # REQ-SHORT-001, ...REQ-SHORT-005
.\src\utils.py                    1           # REQ-SHORT-001, REQ-SHORT-005
.\tests\test_url_shortening.py    70          REQ-ID: REQ-SHORT-005 | ...
.\tests\test_validation.py        27          REQ-ID: REQ-SHORT-005 | ...
```

✅ **You succeeded if:** Every file that mentions REQ-SHORT-005 directly implements, tests, or documents the URL validation requirement — no orphaned reference.

---

### 🔬 Exercise 2: Count Gherkin Scenarios vs. Tests

This exercise shows the spec-to-test coverage ratio.

```powershell
# Count Gherkin scenarios in the spec
(Select-String -Path "specs\url-shortener.yaml" -Pattern "^\s+- id: SCN-").Count

# Count test functions in the test suite
(Select-String -Path "tests\*.py" -Pattern "def test_").Count
```

📊 **Expected output:**
```
10
46
```

✅ **You succeeded if:** You see 10 scenarios (SCN-001 through SCN-010) and 46 test functions — demonstrating that the spec produced roughly 4-5 test functions per Gherkin scenario through the test generator.

---

### 🔬 Exercise 3: Validate a YAML Prompt Template Structure

This exercise proves the `output_schema` field is structurally valid JSON Schema.

```powershell
python -c "
import yaml, json, jsonschema
with open('prompts/code-reviewer.yaml') as f:
    template = yaml.safe_load(f)
schema = template['output_schema']
# A valid JSON schema must have 'type' at the root
print('output_schema type:', schema['type'])
print('required fields:', schema['required'])
print('overall_verdict enum:', schema['properties']['overall_verdict']['enum'])
print('Template version:', template['version'])
print('Tags:', template['tags'])
"
```

📊 **Expected output:**
```
output_schema type: object
required fields: ['review_id', 'file_path', 'overall_verdict', 'findings', 'spec_compliance', 'checked_at']
overall_verdict enum: ['APPROVE', 'APPROVE_WITH_FIXES', 'BLOCK']
Template version: 1.0.0
Tags: ['security-review', 'owasp', 'ssrf', 'code-quality', 'vulnerability-assessment', 'spec-compliance', 'cwe', 'appsec']
```

✅ **You succeeded if:** You see the three-value enum for `overall_verdict` and all required fields — confirming the template enforces structured output.

---

### 🔬 Exercise 4 (Optional): Run Tests to Verify Spec Coverage

```powershell
python -m pytest tests/ -v --tb=no -q
```

📊 **Expected output:**
```
46 passed in X.XXs
```

✅ **You succeeded if:** All 46 tests pass — proving that every Gherkin scenario in the spec has a passing test implementation.

---

## 📚 Interview Preparation

### Q: What is the difference between a functional requirement and an acceptance criterion?

**A:** A functional requirement states *what* the system must do at a behavioral level: "The system MUST shorten a valid URL and return a 6-character code." An acceptance criterion makes that requirement testable and measurable: "POST /urls with a valid URL returns HTTP 201 with a `short_code` field of exactly 6 characters [a-zA-Z0-9]." Acceptance criteria are the bridge between the spec and the test suite — if a criterion can't be expressed as a test assertion, it's not specific enough and needs to be rewritten.

*Why this answer works:* It shows you understand that "done" means provably correct, not just "it runs."

---

### Q: Why version a prompt template (e.g., version: "1.0.0") when you can just update it?

**A:** Prompt templates produce artifacts — security reviews, architecture plans, test suites. If the template changes between the time you generated a review (v1.0.0) and the time you re-run it (v1.1.0), you need to know whether a difference in findings reflects a real code change or a prompt change. Versioning lets you pin: "REV-001 was generated by code-reviewer.yaml v1.0.0." Without versioning, you can't reproduce a past review, which means you can't distinguish "we fixed this" from "the prompt changed and it no longer checks for this."

*Why this answer works:* It frames versioning as an audit and reproducibility concern — exactly the framing a security engineer would use.

---

### Q: How does spec-driven development handle a mid-sprint requirement change?

**A:** You update the spec first — add the new REQ-ID, write its Gherkin scenarios and acceptance criteria, update the API contract if the new requirement adds an endpoint. Then you diff the spec to identify which existing files reference the affected area. Then you implement and add tests. The key property is that the scope of any change is visible *before* implementation begins: a new field on the data model, a new validation check in `validate_url()`, a new test scenario. Without a spec, the change happens ad-hoc and the impact is only fully understood after the code is written.

*Why this answer works:* It demonstrates that SDD provides impact analysis, not just documentation.

---

## ✅ Key Takeaways

- Spec-driven development is the engineering equivalent of writing an IR playbook before the incident: the expected behavior is defined, verifiable, and auditable before any action is taken
- SHALL/MUST normative language (RFC 2119) eliminates requirement ambiguity the same way a SIEM alert rule eliminates ambiguity about what constitutes an incident
- Gherkin scenarios translate directly to test assertions: each `Then` clause is one `assert`
- YAML prompt templates enforce consistent AI output structure the same way a JSON schema enforces consistent API response structure
- Requirement ID traceability (REQ-SHORT-XXX) creates a three-way link between spec, code, and test — answering "does this code do what we promised?" in seconds

---

## 📋 Quick Reference Card

| Item | Value |
|------|-------|
| Spec file | `specs/url-shortener.yaml` |
| Prompt templates | `prompts/spec-writer.yaml`, `prompts/architect.yaml`, `prompts/code-reviewer.yaml`, `prompts/test-generator.yaml` |
| Requirement IDs | REQ-SHORT-001 through REQ-SHORT-006 |
| Gherkin scenarios | SCN-001 through SCN-010 |
| Normative vocabulary | SHALL/MUST (required), SHOULD (recommended), MAY (optional) |
| Template syntax | `{{ variable }}` for parameterization |
| Output schema format | JSON Schema (type, required, properties, enum) |
| Traceability check | `Get-ChildItem -Recurse | Select-String "REQ-SHORT-NNN"` |

---

## 📌 Implemented vs. Recommended

### What This Project Implements ✅
- Full YAML spec with normative language, Gherkin, API contract, and NFRs (`specs/url-shortener.yaml`)
- 4 versioned YAML prompt templates with parameterized task and output_schema (`prompts/*.yaml`)
- REQ-ID comments in every source file (`src/*.py`)
- REQ-ID and scenario ID in every test docstring (`tests/*.py`)

### General Best Practices — Not Implemented Here
- **Spec review gate in CI** — a GitHub Action that rejects PRs if a changed source file doesn't have a matching REQ-ID comment — `Recommended (not implemented here)`
- **Machine-validated Gherkin** — using a BDD framework like `pytest-bdd` that reads the YAML spec directly and runs the Given/When/Then steps as test code — `Recommended (not implemented here)`
- **Automated traceability matrix generation** — a script that builds `docs/traceability-matrix.md` from AST parsing of test docstrings rather than manual authoring — `Recommended (not implemented here)`

---

## 🚀 Ready for Lesson 02?

Next up: **The Vault and the Ledger — SQLAlchemy + FastAPI Data Layer** — where you'll see how the spec's data model becomes Python ORM models, how the CRUD layer protects the database from business logic, and how FastAPI wires it all together with dependency injection. Get ready to trace a URL from HTTP request body to database row and back out as a 302 redirect!

**Optional deeper dive:** Read RFC 2119 (4 pages — the source of SHALL/MUST/SHOULD vocabulary). It's the foundation of every internet protocol spec and every well-written engineering requirement.

**Modification challenge:** Add a new Gherkin scenario to `specs/url-shortener.yaml` for the edge case "URL submitted with trailing whitespace is treated identically to the URL without whitespace." Write the scenario (Given/When/Then), then write a failing test that validates it, then check whether `src/utils.py:validate_url()` already handles it (hint: it does — `url.strip()` is on line 64). Verify the test passes.

*Remember: every line of code without a requirement is a liability — it exists without justification and can be removed without accountability.* 🛡️
