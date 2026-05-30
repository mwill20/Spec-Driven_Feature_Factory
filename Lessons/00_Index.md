# Lesson Index — URL Shortener Service

**Project:** Spec-Driven Feature Factory (SPEC-SHORT-001)  
**Audience:** Cybersecurity Analyst transitioning to Engineering  
**Theme:** Every engineering decision mapped to a security outcome

## Process Lessons — How This Project Was Built

| # | Title | File | Status |
|---|-------|------|--------|
| P01 | The Approved Change Request — Actual Claude Code Workflow | LessonP01_URLShortener_Workflow.md | ✅ Complete |
| P02 | The Engineering Playbook — Optimal Claude Code Workflow | LessonP02_URLShortener_Optimal_Workflow.md | ✅ Complete |

**Read P01 first.** It reconstructs the 7-phase workflow from git history and session artifacts. P02 identifies the 3 upstream gaps that the optimal workflow prevents, including the architecture document that was committed after code and the AGENTS.md that arrived in a delivery audit instead of at project start.

## Content Lessons — What Was Built

| # | Title | File | Status | Required |
|---|-------|------|--------|----------|
| 00 | Index | 00_Index.md | ✅ Complete | Required |
| 01 | The Blueprint Before the Build — Spec-Driven Development with YAML | Lesson01_Spec_Driven_Development.md | ✅ Complete | Required |
| 02 | The Vault and the Ledger — SQLAlchemy + FastAPI Data Layer | Lesson02_SQLAlchemy_FastAPI_Data_Layer.md | ✅ Complete | Required |
| 03 | The Steel Door — SSRF Prevention and URL Validation Security | Lesson03_SSRF_URL_Validation.md | ✅ Complete | Required |

## How to Use These Lessons

**Process lessons first:** Read P01 before P02. P01 teaches the workflow as it happened; P02 teaches the workflow as it should happen.

**Then content lessons:** Read Content Lesson 01 before Lesson 02. Lesson 03 can be read independently.

Each content lesson includes exercises you run from the project root:
```powershell
# Activate the virtual environment first
.\.venv\Scripts\Activate.ps1
# Then run exercises
python -m pytest tests/ -v
```

## Learning Path

```
Process: P01                    Process: P02
(How it was built)          →   (How it should be built)
7 phases · 2 commits ·          9 phases · /project-init ·
4 bugs caught ·                 /architect before src/ ·
delivery audit needed           /critique on spec ·
                                /repo-standards before commit
       ↓
Content: Lesson 01              Content: Lesson 02              Content: Lesson 03
(Why before code)  →           (Database layer)    →           (Security controls)
spec → plan → impl              models → CRUD → API             validate → block → log
```
