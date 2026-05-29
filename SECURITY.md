# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Yes    |

## Reporting a Vulnerability

To report a security vulnerability in this project, please email:

**mwill.itmission@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested remediation (if known)

You will receive acknowledgement within 48 hours and a full response within 7 days.

**Do not open a public GitHub issue for security vulnerabilities.**

## Security Controls

| Control | Implementation | REQ-ID |
|---------|---------------|--------|
| SSRF prevention | Private IP range blocklist in `src/utils.py:validate_url()` | REQ-SHORT-005 |
| Input validation | URL scheme, format, and length checks | REQ-SHORT-005 |
| Domain blocklist | Database-driven, configurable at startup | REQ-SHORT-005 |
| No hardcoded secrets | All credentials via environment variables | NFR-SECURITY |
| Soft deletion | `is_active = False` preserves audit trail | REQ-SHORT-006 |
| Audit logging | All create/redirect/delete/blocked events logged | NFR-SECURITY |
| Structured errors | No internal details exposed in error responses | REQ-SHORT-006 |

## Known Limitations

1. **DNS resolution not performed at validation time** — URLs like `http://internal.corp.local/` pass validation because the hostname is not an IP literal. DNS-based SSRF requires network-level egress filtering as a compensating control.
2. **No rate limiting in application code** — rate limiting is documented in NFRs but implemented at infrastructure level (reverse proxy). An unprotected instance has no in-app throttling.
3. **No authentication** — all endpoints are publicly accessible. Adding URL ownership and authentication is a future enhancement.
4. **Referrer stores only last value** — the analytics referrer field is overwritten on each redirect; full referrer history requires a separate click_events table.

## Threat Model

See `docs/threat-models/` (TODO: full threat model document — tracked as open item per project init standards).

**Framework:** STRIDE (primary) + OWASP LLM Top 10 supplement  
**Key threats mitigated:** SSRF (T10), injection via URL blocklist (T03), information disclosure via error responses (T06)
