# 🎓 Lesson P02: The Engineering Playbook — Optimal Claude Code Workflow for Web Application Builds

## 🛡️ Welcome, Analyst Turning Engineer!

You've seen how the URL Shortener Service was actually built in Lesson P01 — the spec written from a feature request, the architecture documented after the code, the `AGENTS.md` missing until a delivery audit caught it. Those aren't failures of execution; they're failures of *sequence*. The code works. The tests pass. The security controls are in place. But the artifacts that should have *driven* the build arrived *after* it.

🔍 Today we're looking at what should have happened before Phase 1 of P01's workflow: a structured interview phase, an architecture design committed before any source file, and a critique pass on the spec itself — all before `/principal-engineer` was ever invoked.

> **How this pairs with P01:** P01 shows what was done. This lesson shows what should have been done first. The tools are the same. The discipline — and the sequence — is different.

---

## 🎯 Learning Objectives

By the end of this lesson you will be able to:

1. Run a `/project-init` interview prompt and explain why it precedes spec writing rather than following it
2. Write a spec table with full acceptance criteria populated from a project's deliverables — in the format that `/critique` will evaluate
3. Apply `/critique` to a spec document (not just code) and describe what class of findings it surfaces that code review cannot
4. Explain the architectural significance of committing `docs/ARCHITECTURE.md` before `src/` exists
5. Use the "Optimal vs. Actual" table in this lesson to identify which gaps in P01's workflow each optimal phase prevents

**Time estimate:** 50 minutes | **Companion:** `Lessons/LessonP01_URLShortener_Workflow.md`

---

## 🧠 What This Lesson Is About — Plain English

The spec-first discipline in P01 was real: a formal specification preceded the code, YAML prompt templates versioned the AI instructions, and the self-critique loop caught two HIGH severity bugs before any user could trigger them. The problem isn't that the process lacked structure. The problem is that the structure started at the *wrong phase*.

When `docs/ARCHITECTURE.md` is written after the code, it describes what exists rather than constraining what gets built. When `AGENTS.md` arrives in a delivery audit commit rather than at project start, there are no documented rules governing AI assistant behavior during the sprint that built the code. When `/critique` runs on implementation files but not on the spec, the spec's ambiguities become implementation bugs — FIND-001 is the evidence.

The optimal workflow inserts three upstream phases before the spec is written: a structured interview to extract requirements from the person who knows them (not just from the PM's summary), an architecture design that is committed and critiqued before implementation begins, and a spec interrogation pass that turns ambiguous SHALL statements into unambiguous acceptance criteria before a single line of code answers to them.

**Real-world analogy:** In a SOAR deployment, you never automate a response playbook before mapping the manual process first. The fastest way to automate the wrong behavior is to skip the "describe what a skilled analyst does by hand" phase. The URL Shortener Service automated correctly because the spec was detailed — but the spec was only as detailed as the feature request that drove it. An interview would have surfaced the questions the feature request never asked: "What happens when a blocklist entry is added while the service is running? What does expiry mean when requests arrive at exactly the expires_at timestamp? Who owns the SSRF blocklist update process?"

---

## 🔵🟡🔴 Career Lens

### 🔵 Analyst Lens — The Interview as an Escalation Brief

When a new alert type appears in FortiSIEM, the first step isn't writing a correlation rule — it's writing an escalation brief: what is the observable behavior, what does a true positive look like, what does a false positive look like, what information do you need to triage it, and what response actions are authorized? The brief captures the analyst's knowledge before the rule attempts to encode it.

The `/project-init` interview serves exactly this function. It captures the product owner's knowledge before the spec attempts to encode it. Without the interview, the spec can only encode what the feature request explicitly said. With the interview, the spec encodes what the product owner *knows but didn't think to write down* — edge cases, security requirements, data lifecycle questions, and constraints that appear obvious in conversation but invisible in a written request.

**The practical difference:** In P01, REQ-SHORT-005's SSRF controls appeared in the spec because the spec author knew to include them. If the spec author hadn't known about SSRF, those controls would be absent — and no amount of self-critique on the implementation would add them, because the reviewer checks against requirements, not against the author's knowledge. The interview makes threat surface explicit before the spec is written.

### 🟡 Engineer Lens — The Spec as an Immutable Build Contract

In spec-driven development, the spec is not a reference document — it is the source of truth that outranks every other artifact. "Spec is immutable during build" means: when the implementation encounters a gap or ambiguity in the spec, the correct response is to stop and update the spec, not to interpret and proceed. Implementation decisions that aren't grounded in a spec entry are either spec gaps (the feature is real but unwritten) or scope creep (the feature shouldn't exist yet).

The AGENTS.md file that governs this repository makes this explicit:

> "If a requested change requires a new requirement, add it to the spec first, then implement. Never silently extend behavior beyond what the spec defines."

This rule exists because silent extensions are invisible to `/overseer`, the traceability matrix, and any future developer trying to understand why a behavior exists. The immutability constraint is not bureaucracy — it's the mechanism that keeps the traceability chain intact from requirement to code to test.

**Engineering decision to own:** In P01's workflow, `docs/implementation-plan.md` was generated using `prompts/architect.yaml` and lists TASK-002's acceptance criterion as "Private IP check uses `try/except/else` to prevent exception inheritance bypass." But FIND-001 proved the initial code did *not* implement this. The plan was committed in the delivery audit after the fix was already applied — making it a post-hoc description, not a pre-implementation constraint. When the plan is committed before code, the TASK-002 acceptance criterion becomes a *gate*: `/overseer` checks the task output against it, and the task is not marked complete until the `try/except/else` pattern is present.

### 🔴 AI Security Lens — Threat Model Before Architecture

For a web application like this URL shortener, the right threat modeling framework is STRIDE (data flows, trust boundaries) supplemented by OWASP ASVS (verification requirements for the API surface). The project's `specs/url-shortener.yaml` NFR section captures several STRIDE mitigations — but without a formal threat model, there is no structured enumeration of threats, no "what did we miss?" analysis, and no documented residual risk decision.

The self-critique log's "What the Reviewer Missed" section is doing threat model work informally: URL redirect chaining, referrer-overwrite data loss, and route resolution ordering fragility are all legitimate threats. In a formal threat model, each would have: a threat description, a likelihood and impact rating, a mitigation pointer to specific code, and a residual risk decision. Without the formal structure, these gaps are documented but unactionable — no owner, no target date, no explicit accept/mitigate decision.

For an AI/ML extension of this service (e.g., adding an AI-powered URL reputation scoring system), ATLAS (MITRE's adversarial ML framework) would need to be layered on top of STRIDE: model evasion via adversarially crafted URLs, data poisoning of the blocklist training set, and model inversion to expose the blocked domains list.

---

## 🗺️ The 9-Phase Optimal Workflow

```
Phase 0           Phase 1           Phase 2
PROJECT SETUP  →  INTERVIEW      →  SPEC WRITING
/project-init     Structured Q&A    spec-writer.yaml
AGENTS.md         before any spec   AFTER interview
.env.example      extracts edge     captures what the
CLAUDE.md         cases + threats   feature request
                                    didn't say
      │
      ▼
Phase 3           Phase 4           Phase 5
ARCHITECTURE   →  SPEC          →  THREAT MODEL
DESIGN            INTERROGATION     /threat-model
/architect        /critique         STRIDE + OWASP ASVS
BEFORE code       on spec, not      docs/threat-models/
produces          code first        THREAT_MODEL.md
ARCHITECTURE.md                     BEFORE code
      │
      ▼
Phase 6           Phase 7           Phase 8
BUILD          →  VERIFY         →  PUBLISH
/principal-       /overseer         /repo-standards
engineer          each sprint task  catches AGENTS.md,
sprint against    against spec      .env.example,
confirmed spec    acceptance        LIMITATIONS.md gaps
                  criteria          BEFORE commit
      │
      ▼
Phase 9
KNOWLEDGE CAPTURE
/lesson-gen → content lessons
/workflow-lesson-gen → P01/P02
traceability matrix (REQ → code → test)
```

---

## 🔑 Key Concepts

### 1. The Interview as Threat Surface Elicitation

The interview phase is not just requirements gathering — it is structured threat surface elicitation. The questions that reveal the most security-relevant information are not "what should the system do?" but "what should the system refuse to do?", "what happens when a dependency is unavailable?", and "who can perform each action, and what is the worst case if they're wrong?"

**When it matters:** In P01, the SSRF controls appeared in the spec because the spec author knew to include them. In an interview, those controls would be surfaced by specific questions: "This service will accept user-submitted URLs — what classes of URLs must be rejected and why?" An author who doesn't know about SSRF answers "invalid URLs and already-shortened URLs." An interview that asks the right questions surfaces SSRF even from someone who has never heard of SSRF.

### 2. Design-Time vs. Documentation-Time Architecture

Architecture produced at design time constrains the implementation. Architecture produced at documentation time describes it. The distinction is not about document quality — both can be accurate and well-written. The distinction is about causality: a design-time architecture is a *commitment* the implementation must satisfy; a documentation-time architecture is a *description* of what the implementation chose.

`docs/implementation-plan.md` is accurate and detailed. But because it was committed in the delivery audit after the code existed, the acceptance criterion "Private IP check uses `try/except/else`" in TASK-002 is retrospective. It describes what the correct implementation looks like; it did not prevent the incorrect implementation from being built first.

### 3. Spec Interrogation — Critique Before Build

`/critique` is typically invoked on code — that's where it was used in P01 (code-reviewer.yaml on `src/utils.py`, `src/routers/urls.py`, `src/crud.py`). But spec interrogation applies the same adversarial skepticism to the spec document before any code is written.

A spec critique asks: "Which requirements are ambiguous? Which acceptance criteria are unmeasurable? Which edge cases are implied but not stated? What security surface is described but not specified with sufficient detail to implement defensively?" FIND-001 exists because REQ-SHORT-005 said "reject private IPs" without specifying how the validation exception must be structured to prevent bypass. A spec critique would have added "validation MUST NOT use a broad `except` handler that can catch `UrlValidationError`" as an acceptance criterion — and FIND-001 would have been caught at spec review, not at code review.

---

## 📝 Phase-by-Phase Walkthrough

### Phase 0: Project Setup

Before any spec, any interview, or any code: initialize the project infrastructure. In P01, `AGENTS.md`, `.env.example`, `LIMITATIONS.md`, `docs/ARCHITECTURE.md`, and `docs/implementation-plan.md` were all missing from the initial delivery. A `/project-init` run at Phase 0 produces these before implementation begins.

**Commands:**
```powershell
# In the project root
specify init --here --integration claude   # scaffolds specs/ and Claude-aware agent instructions
```

**Files produced by Phase 0:**
- `AGENTS.md` — AI assistant behavior rules (never bypass validation, spec before code)
- `.env.example` — safe placeholder values for all required env vars
- `CLAUDE.md` (project-level) — project-specific context for Claude Code
- `docs/LIMITATIONS.md` — what the project cannot do; when not to use it

These files govern the entire build. If they don't exist at project start, they cannot constrain the sprint that produces the code they're supposed to govern.

> **P01 gap:** `AGENTS.md` was committed in the delivery audit (commit 2). The rule "database queries belong ONLY in `src/crud.py`" didn't exist as a documented constraint during the sprint that built `src/crud.py`.

---

### Phase 1: The Interview

Before writing a single spec requirement, conduct a structured interview using `/project-init` — Phases A through H.

**Full interview prompt (verbatim):**
```
I'm starting a new project in this directory. Before you write a spec or any code,
interview me about this project using the /project-init workflow. I want to establish:
- What this service does and who its users are
- The threat surface: what classes of input must be rejected, and why
- The data model and persistence requirements
- The API contract: every endpoint, status code, and response schema
- Security requirements: authentication, validation, audit logging, rate limiting
- The acceptance criteria I'll use to call this service production-ready
- Non-functional requirements: performance, availability, and operational constraints

Ask me questions one group at a time. Wait for my answers before proceeding.
Do not generate a spec until I have answered all groups.
```

**What the interview produces that P01's spec lacked:**

P01's spec was written from "Build a URL shortener that shortens URLs, redirects users, and tracks click analytics." The SSRF requirements were included because the spec author knew to add them. An interview surfaces them through questions:

- *"This service accepts user-submitted URLs. What categories of URLs must be rejected?"* → Prompts the product owner to list invalid formats, private IPs, and blocked domains — making SSRF a stated requirement from the product owner, not a spec author addition.
- *"What happens when a URL is submitted that's already in the system?"* → Surfaces the idempotency behavior (REQ-SHORT-001 acceptance criteria: "same URL submitted twice returns same short code") explicitly.
- *"What is the analytics model? Does each redirect create an event, or update a single record?"* → Surfaces the referrer-overwrite limitation that P01's reviewer missed — before it becomes an accepted technical debt item.

**How the interview changes the spec:** P01's `specs/url-shortener.yaml` is thorough. An interview-driven version would additionally include: an explicit requirement for the analytics data model (click event history vs. aggregate record), an explicit requirement for the SSRF validation exception hierarchy pattern, and an explicit constraint on blocklist update behavior (runtime-addable without code deployment — which is in the ARCHITECTURE.md but not in the spec requirements).

---

### Phase 2: Spec Writing

After the interview, generate the spec using `prompts/spec-writer.yaml`. The interview output becomes the `{{ feature_request }}` injection — but it is now a detailed product owner transcript, not a two-line summary.

**Good spec table — populated with this project's actual deliverables:**

| Deliverable | Format | Path | Acceptance Criteria |
|------------|--------|------|---------------------|
| Functional specification | YAML | `specs/url-shortener.yaml` | ≥6 REQ-IDs with MUST/SHALL priority; ≥10 Gherkin scenarios; full OpenAPI API contract; security NFRs including SSRF and rate limiting |
| ER diagram | Mermaid | `specs/diagrams/er.md` | All tables, fields, types, constraints, and foreign key relationships documented |
| State diagram | Mermaid | `specs/diagrams/state.md` | All URL lifecycle states including DELETED; all transitions with guard conditions |
| Sequence diagram | Mermaid | `specs/diagrams/sequence.md` | POST /urls flow and GET /{code} redirect flow; error paths (422, 410, 404) shown |
| Architecture document | Markdown | `docs/ARCHITECTURE.md` | Component diagram, data flow narrative, design decisions with rationale; committed BEFORE `src/` |
| Implementation plan | Markdown | `docs/implementation-plan.md` | TASK-NNN breakdown; each task has REQ refs, acceptance criteria, and estimated effort; committed BEFORE `src/` |
| AGENTS.md | Markdown | `AGENTS.md` | Spec-before-code rule; REQ-ID traceability requirement; CRUD boundary rule; prohibited actions; validation command |
| Implementation | Python | `src/` | All files cite REQ-IDs; CRUD boundary respected; no raw queries in routers |
| Test suite | Python | `tests/` | 46 tests; 100% pass rate; all docstrings cite REQ-ID and Scenario-ID |
| Traceability matrix | Markdown | `docs/traceability-matrix.md` | All 6 REQ-IDs: code location + test function + pass status |

The critical rows here are Architecture and Implementation plan — both must be committed as `BEFORE src/` deliverables, not after.

---

### Phase 3: Architecture Design

Invoke `/architect` after the spec is confirmed but before any `src/` files exist.

**`/architect` prompt:**
```
Using /architect, generate a complete technical implementation plan for the spec at
specs/url-shortener.yaml. The target stack is Python 3.12 + FastAPI + SQLAlchemy 2.0
+ SQLite + pytest. Produce:
1. A component diagram with trust boundaries
2. A data flow narrative for POST /urls and GET /{code}
3. Numbered TASK-NNN breakdown with REQ refs and measurable acceptance criteria
4. Directory layout showing every file before it is created
5. Pinned dependency list

Commit docs/ARCHITECTURE.md and docs/implementation-plan.md BEFORE any src/ files.
These are design constraints, not documentation artifacts.
```

**What changes when architecture comes first:**

In P01, TASK-002's acceptance criterion "Private IP check uses `try/except/else` to prevent exception inheritance bypass" was written after FIND-001's fix was applied. If this criterion had been committed before implementation, `/overseer` would have checked the TASK-002 output against it before marking the task complete. The criterion would have caught FIND-001 at task verification, not at code review.

At design time, `/architect` would also have flagged: the datetime timezone normalization pattern needed for SQLite integration (FIND-002's root cause). A design that specifies "SQLite returns naive datetimes; all expiry comparisons must normalize using `.replace(tzinfo=timezone.utc)` before comparison" would have made FIND-002 a task acceptance criterion violation rather than a hidden integration gotcha.

---

### Phase 4: Spec Interrogation

Before invoking `/principal-engineer` to build, run `/critique` on `specs/url-shortener.yaml` — not on code.

**`/critique` prompt for the spec:**
```
Using /critique, review specs/url-shortener.yaml as a security-focused specification
auditor. Return APPROVE / APPROVE WITH FIXES / BLOCK.

Check for:
- Requirements with acceptance criteria that are measurable but underspecified
  (e.g., "reject private IPs" without defining the exact exception handling pattern)
- Gherkin scenarios with Then clauses that are ambiguous about response body shape
  (e.g., "contains error detail" without specifying the field name)
- Security requirements that name a control but don't specify the implementation
  constraint needed to prevent bypass
- Missing requirements implied by the diagrams but not written as REQ-IDs
- NFRs (rate limiting, headers) that are documented but not referenced by any REQ-ID
```

**Findings this would have produced for this spec:**

| Finding | Location in Spec | Severity | Recommended Fix |
|---------|-----------------|----------|-----------------|
| REQ-SHORT-005 says "reject private IPs" but does not specify that the validation exception must not be catchable by a broad ValueError handler | `requirements[4].acceptance_criteria` | HIGH | Add: "The IP validation MUST be structured so that `UrlValidationError` cannot be silently swallowed by an exception handler intended for `ipaddress` library errors." |
| SCN-007's Then clause says "contains error field 'BLOCKED' and the blocked domain" — test-generator.yaml will verify the status code (400) but may not assert the response body content without an explicit field reference | `scenarios[6].then[1]` | MEDIUM | Rewrite as: "the response body contains `{\"error\": \"BLOCKED\", \"detail\": {\"domain\": \"malware.example.com\"}}`" |
| Analytics update behavior on expired redirect not stated in any REQ-ID — implied by sequence diagram but not written | Missing REQ-ID | MEDIUM | Add explicit acceptance criterion to REQ-SHORT-003: "Click count MUST NOT increment when a redirect request is rejected with 410 due to URL expiry." |
| Rate limiting is in the NFR section (`nfr.rate_limiting`) but no REQ-ID references it — the traceability matrix cannot cover it | `nfr.rate_limiting` | LOW | Add REQ-SHORT-007 or reference the NFR block from an existing REQ-ID. |

FIND-001 would have been caught at Phase 4, not Phase 5. The second finding — SCN-007 response body assertion — is precisely the test coverage gap noted in REPORT.md Q11: "The test asserts the 400 status but doesn't inspect the response body for the domain name."

---

### Phase 5: Threat Model

After the spec is approved but before `/principal-engineer`, invoke `/threat-model`.

**Framework selection for this project:** STRIDE primary (REST API with data flows, trust boundaries, SQLite persistence) + OWASP ASVS supplementary (API security verification requirements).

**`/threat-model` prompt:**
```
Using /threat-model, produce a threat model for the URL Shortener Service at
specs/url-shortener.yaml. Select the appropriate framework and justify in one sentence.
Output to docs/threat-models/THREAT_MODEL.md. Enumerate threats per framework
category. For each threat, provide: likelihood (L/M/H), impact (L/M/H), severity,
and a mitigation pointer to a specific function or file in src/ (or a TODO if not yet
implemented). Document residual risks with an explicit accept/mitigate/transfer
decision.
```

**What a STRIDE threat model would formalize that the self-critique log documents informally:**

The self-critique log's "What the Reviewer Missed" section contains three undocumented threats:
1. URL redirect chaining (`https://bit.ly/x` bypasses single-level SSRF) → STRIDE: Spoofing + SSRF
2. Referrer-overwrite data loss → STRIDE: Tampering on analytics integrity
3. Route resolution ordering dependency → STRIDE: Elevation of privilege (if order changes, `/api/urls/{code}` becomes inaccessible)

Each of these is a legitimate threat that needs an explicit accept/mitigate decision with an owner. As noted in the self-critique log, these are "accepted risks" — but the acceptance is informal and unowned. A threat model formalizes that decision and creates an audit trail.

---

### Phases 6–9: Build, Verify, Publish, Knowledge Capture

These phases parallel P01's Phases 4–7, with one critical difference: every task now references a spec entry, and `/overseer` verifies each task's output against its acceptance criteria before moving to the next task.

**Phase 6 — Build:**
```
/principal-engineer sprint:
Task: TASK-002 — URL Validation and Code Generation
Spec: specs/url-shortener.yaml REQ-SHORT-001, REQ-SHORT-005
Implementation plan: docs/implementation-plan.md TASK-002
Acceptance criteria: [list from plan]
Do not proceed to TASK-003 until TASK-002 passes all acceptance criteria.
```

**Phase 7 — Verify:**
```
/overseer: check the output of TASK-002 against docs/implementation-plan.md TASK-002
acceptance criteria. Specifically verify:
- generate_short_code() returns exactly 6 chars from [a-zA-Z0-9]
- validate_url() raises UrlValidationError for private IPs (test: test_reject_private_ip_returns_422)
- Private IP check uses try/except/else — not try/except with broad ValueError handler
- hash_url() returns SHA-256 hex digest
Report PASS or FAIL for each criterion. Do not mark COMPLETE until all criteria pass.
```

Under `/overseer`, the TASK-002 criterion "Private IP check uses `try/except/else`" would have been a gate. The task would have returned FAIL on the criterion check, the fix would have been applied before the task was marked complete, and FIND-001 would never have made it to Phase 5 (self-critique).

**Phase 8 — Publish:**
```
/repo-standards: audit this repository before committing. Check for:
- README.md (present)
- SECURITY.md (present)
- AGENTS.md (missing until delivery audit — CATCH)
- .env.example (missing until delivery audit — CATCH)
- docs/LIMITATIONS.md (missing until delivery audit — CATCH)
- docs/ARCHITECTURE.md (missing until delivery audit — CATCH)
- .gitignore (present)
- LICENSE (TODO placeholder if missing)
Report all missing files before any commit is created.
```

Every file that appeared in P01's delivery audit commit would be caught by `/repo-standards` before the initial commit — not after.

**Phase 9 — Knowledge Capture:**
```
/lesson-gen: generate educational lessons for Lesson01, Lesson02, Lesson03 from src/
/workflow-lesson-gen: generate P01 and P02 workflow lessons for this project
```

---

## 📌 Optimal vs. Actual: What Changed

| Moment | What Actually Happened (P01) | What Should Have Happened (P02) | Cost of the Gap |
|--------|-----------------------------|---------------------------------|-----------------|
| **Before spec writing** | PM feature request → spec directly; SSRF controls included because spec author knew to add them | `/project-init` interview → spec author asks "what classes of URLs must be rejected?" → SSRF explicitly stated by product owner | Spec quality depended on author's domain knowledge. A different author produces a spec without SSRF controls. |
| **Architecture and implementation plan** | `docs/ARCHITECTURE.md` and `docs/implementation-plan.md` committed in delivery audit (commit 2), after code | `/architect` produces both files before `src/` is created; committed as design constraints | TASK-002 acceptance criterion "try/except/else" was retrospective; FIND-001 was not caught at task verification. 12 lines of fix applied in Phase 5 instead of Phase 6 gate. |
| **Spec interrogation** | `/critique` run on implementation code (Phase 5 of P01) | `/critique` run on `specs/url-shortener.yaml` before Phase 6 (build) | REQ-SHORT-005 ambiguity ("reject private IPs" without specifying exception hierarchy pattern) became FIND-001 in code review. SCN-007 response-body assertion gap became a documented coverage gap in REPORT.md Q11. |
| **Repo standards** | `AGENTS.md`, `.env.example`, `LIMITATIONS.md` missing from initial commit; delivery audit required | `/repo-standards` before initial commit catches all five missing files | Delivery audit commit required. `AGENTS.md` rules (CRUD boundary, spec-before-code) were not documented as constraints during the sprint that built the code they govern. |
| **Threat model** | Security requirements in NFR section; "What the Reviewer Missed" documents 3 undocumented threats | `/threat-model` (STRIDE + OWASP ASVS) produces `docs/threat-models/THREAT_MODEL.md` | URL redirect chaining, referrer-overwrite, and route resolution ordering are informal accepted risks with no owner, no explicit decision, and no target date for reassessment. |

---

## 🧪 Hands-On Exercises

### Exercise 1: Run the Interview Phase

**Goal:** Experience what a `/project-init` interview surfaces that a feature request alone doesn't.

Copy the following prompt into a fresh Claude Code session pointed at this project directory:

```
I'm building a new URL shortener service. Before writing a spec or any code,
interview me about this project. I want to establish: what the service does and
who uses it; what categories of URLs must be rejected and why; the data model;
the API contract with every status code; security requirements including validation
and rate limiting; and the acceptance criteria for "production ready."

Ask one group of questions at a time. Wait for my answers. Do not write a spec
until all groups are answered.
```

**Success criterion:** Count the questions that the interview generates which do NOT appear as explicit requirements in `specs/url-shortener.yaml`. These are the implicit requirements that the spec's author already knew — but that a different author would have missed.

---

### Exercise 2: Write a Spec Table with Acceptance Criteria

**Goal:** Practice writing spec entries in the format that `/critique` will evaluate.

Write a spec table entry for a hypothetical new requirement: "The service MUST support click event history — storing a separate record for each redirect, not overwriting a single row." This addresses the referrer-overwrite gap documented in `docs/self-critique-log.md`'s "What the Reviewer Missed" section.

Use this format:
```yaml
- id: REQ-SHORT-007
  priority: SHALL
  statement: >
    [Write your requirement statement here using SHALL/MUST language]
  rationale: [Why this requirement exists — what problem it solves]
  acceptance_criteria:
    - "[Measurable criterion 1 — pass/fail verifiable]"
    - "[Measurable criterion 2]"
    - "[Measurable criterion 3 — the edge case]"
```

**Success criterion:** Each acceptance criterion must be testable with a single `assert` statement in a pytest function. If you can't write the assert, the criterion is not specific enough.

---

### Exercise 3: Apply `/critique` to the Spec

**Goal:** Practice running adversarial spec review before any implementation begins.

```powershell
# In a fresh Claude Code session pointed at this project
# Run the following prompt:
```

```
Using /critique, review specs/url-shortener.yaml as a specification auditor.
Return APPROVE / APPROVE WITH FIXES / BLOCK.

Look for:
1. Acceptance criteria that describe observable behavior but not defensive
   implementation constraints (e.g., "reject private IPs" without specifying
   how the exception hierarchy must be structured)
2. Gherkin Then clauses that a test generator could implement with a status-code
   check alone, but that actually require response body verification
3. Requirements implied by diagrams in specs/diagrams/ but not written as REQ-IDs
4. NFRs in the nfr: section that have no corresponding REQ-ID reference

For each finding: state the spec location, the severity, and the exact text change
that would make the criterion unambiguous.
```

**Success criterion:** The critique should surface at least 2 findings that match items in the "Spec Interrogation" section of this lesson. If it surfaces findings that are NOT in this lesson, those are genuine discoveries — document them.

---

### Exercise 4: Run `/repo-standards` Before Committing

**Goal:** Experience the delivery audit that should happen before `git commit`, not after.

Run the following in a Claude Code session:

```
Using /repo-standards, audit this repository for publication readiness. Check:
- README.md, SECURITY.md, AGENTS.md, .env.example, .gitignore — present?
- docs/ARCHITECTURE.md, docs/LIMITATIONS.md — present and complete?
- LICENSE — present? (use TODO placeholder if missing)
- No secrets, real credentials, or internal paths in any committed file

Report: which files are present, which are missing, which have content gaps.
Do not consider this audit complete until every required file is present or has
a documented reason for absence.
```

**Success criterion:** Compare the output to the files listed in P01's delivery audit (commit 2). Every file in that commit should appear in the audit report as "would have been caught before initial commit."

---

## 📚 Interview Preparation

### 🟡 Cybersecurity Engineering Interview

**Q: You mentioned that the architecture document for this project was written after the code, not before it. Why does that distinction matter in a security context, and how would you prevent it on a team?**

**A:** An architecture document written after code is accurate but non-binding — it describes what the implementation chose, rather than constraining what it could choose. In a security context, the most important architecture decisions are the ones that prevent entire classes of vulnerabilities: where trust boundaries sit, which components can reach the database, how validation exceptions propagate. When those decisions are documented before implementation, they are enforceable via acceptance criteria in the implementation plan and verifiable by `/overseer`. When documented after, they are historical records that future developers may or may not follow.

On a team, I'd enforce this by making the architecture commit a prerequisite for the first sprint task: the PR gate requires that `docs/ARCHITECTURE.md` and `docs/implementation-plan.md` exist and are approved before any `src/` file is mergeable. The architecture review is the design review — it's not a documentation task.

### 🔴 AI Security Engineering Interview

**Q: You describe a /critique pass on the spec before implementation begins. For an AI system — say, the URL shortener extended with an AI-powered URL reputation scorer — what additional items would you add to the spec critique checklist that a standard web application critique wouldn't cover?**

**A:** For an AI component, the spec critique checklist gains three AI-specific categories:

First, **adversarial input requirements**: the spec must explicitly enumerate how the AI model's output is used in security decisions. For URL reputation scoring, "if the model returns HIGH risk, reject the URL" is a security-relevant action — the spec must state the deterministic fallback when the model is unavailable, overloaded, or returns an out-of-distribution confidence score.

Second, **indirect prompt injection surface**: if the AI model processes any content retrieved from submitted URLs (e.g., page titles, metadata), the spec must explicitly address what attacker-controlled content could be injected into the model's context via a malicious URL's metadata. The spec's acceptance criteria must state: "The model MUST NOT act on instructions embedded in page content retrieved from submitted URLs."

Third, **model output validation gate**: the spec must require that AI model outputs pass through a deterministic validation layer before influencing any security decision, database write, or irreversible action. "The model said so" is never a sufficient acceptance criterion for a security-relevant behavior — the spec must name the rule-based gate that validates the output before it is acted upon.

---

## ✅ Key Takeaways

1. **The interview phase makes threat surface explicit before the spec can omit it.** In P01, SSRF controls appeared in the spec because the author knew to add them. An interview surfaces them from the product owner, not the author's domain knowledge — which means they're present regardless of who writes the spec.

2. **Architecture committed before code is a design constraint; committed after is documentation.** TASK-002's acceptance criterion "try/except/else" was retrospective in P01. As a pre-build commitment enforced by `/overseer`, it would have been a gate — FIND-001 would never have made it to Phase 5.

3. **`/critique` on the spec catches a different class of bugs than `/critique` on the code.** Code review found that the SSRF check was broken; spec review would have found that the spec gave no guidance on how to structure the exception hierarchy, which is why it was broken. The spec gap produced the code bug.

4. **`/repo-standards` before commit, not delivery audit after.** Five files that appeared in P01's commit 2 (AGENTS.md, .env.example, LIMITATIONS.md, ARCHITECTURE.md, implementation-plan.md) would have been caught by `/repo-standards` before the initial commit. Delivery audits are acceptable when `/repo-standards` wasn't run; they're avoidable when it was.

5. **Informal accepted risks need formal ownership.** The three threats documented in P01's "What the Reviewer Missed" section (URL redirect chaining, referrer-overwrite, route resolution ordering) are legitimate risks. Without a threat model, they have no owner, no explicit decision, and no target date for reassessment. A formal threat model turns "we know about this" into "we've decided to accept/mitigate/transfer this, with this rationale, owned by this person, reviewed on this date."

---

## 📋 Quick Reference: Slash Command Selection Guide

| Situation | Command | Why This Command, Not a Plain Prompt |
|-----------|---------|-------------------------------------|
| Starting a new project before writing a spec | `/project-init` | Runs Phases A–H systematically; ensures interview precedes spec; produces AGENTS.md and CLAUDE.md as outputs |
| Designing system architecture before implementation | `/architect` | Produces structured component diagram, data flow, TASK breakdown with acceptance criteria; output is committed as a design constraint, not documentation |
| Reviewing a spec for security gaps before build | `/critique` | Returns APPROVE / APPROVE WITH FIXES / BLOCK with numbered findings and severity; prevents rubber-stamp review |
| Running a sprint against a confirmed spec | `/principal-engineer` | Executes tasks referencing the spec; designed to stop and report gaps rather than interpret around them |
| Verifying a sprint task's output against acceptance criteria | `/overseer` | Checks implementation against the spec's acceptance criteria; gates task completion on measurable evidence |
| Auditing a repo before committing | `/repo-standards` | Checks for README, SECURITY.md, AGENTS.md, .gitignore, LICENSE, docs structure; reports gaps rather than silently accepting them |
| Generating educational content from source files | `/lesson-gen` | Produces structured lessons at the appropriate knowledge level; includes exercises grounded in real project files |
| Generating process documentation from workflow history | `/workflow-lesson-gen` | Reconstructs actual vs. optimal workflow from git history and session artifacts; teaches the process, not just the output |
