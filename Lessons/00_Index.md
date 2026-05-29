# Lesson Index — URL Shortener Service

**Project:** Spec-Driven Feature Factory (SPEC-SHORT-001)  
**Audience:** Cybersecurity Analyst transitioning to Engineering  
**Theme:** Every engineering decision mapped to a security outcome

| # | Title | File | Status | Required |
|---|-------|------|--------|----------|
| 00 | Index | 00_Index.md | ✅ Complete | Required |
| 01 | The Blueprint Before the Build — Spec-Driven Development with YAML | Lesson01_Spec_Driven_Development.md | ✅ Complete | Required |
| 02 | The Vault and the Ledger — SQLAlchemy + FastAPI Data Layer | Lesson02_SQLAlchemy_FastAPI_Data_Layer.md | ✅ Complete | Required |
| 03 | The Steel Door — SSRF Prevention and URL Validation Security | Lesson03_SSRF_URL_Validation.md | ✅ Complete | Required |

## How to Use These Lessons

Read Lesson 01 before Lesson 02. Lesson 03 can be read independently.

Each lesson includes exercises you run from the project root:
```powershell
# Activate the virtual environment first
.\.venv\Scripts\Activate.ps1
# Then run exercises
python -m pytest tests/ -v
```

## Learning Path

```
Lesson 01              Lesson 02              Lesson 03
(Why before code)  →  (Database layer)    →  (Security controls)
spec → plan → impl    models → CRUD → API    validate → block → log
```
