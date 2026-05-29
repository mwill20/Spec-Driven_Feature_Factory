# Limitations — URL Shortener Service

**Spec:** SPEC-SHORT-001 v1.0.0

This document describes what the service cannot do and when not to use it. Every production system has limitations — documenting them is required for honest deployment decisions.

---

## Functional Limitations

### No DNS Resolution at Validation Time
**What this means:** The SSRF protection blocks URLs where the hostname is a literal private IP address (e.g., `http://192.168.1.1/admin`). It does **not** block URLs where a hostname resolves to a private IP via DNS (e.g., `http://internal-db.corp.local/`).

**Impact:** A determined attacker who controls a public DNS entry could point `attacker.com` to `192.168.1.1` and bypass the SSRF check.

**Compensating control required:** Egress firewall rules that prevent the application server from making connections to RFC 1918 ranges.

---

### Referrer Stores Only the Last Value
**What this means:** Each redirect overwrites `referrer` with the current request's `Referer` header. If a URL is clicked from five different referrers, only the last one is stored.

**Impact:** Analytics are incomplete. Full referrer history requires a separate `click_events` table (one row per click).

**Workaround:** For full analytics, add a `click_events` table and append a row on every redirect instead of overwriting `referrer` on the parent record.

---

### No Authentication or Ownership
**What this means:** Any client can shorten any URL, retrieve analytics for any code, or delete any short URL. There is no concept of URL ownership or user accounts.

**Impact:** Not suitable for multi-tenant production use without adding authentication (e.g., API keys, OAuth2) and per-user access control.

---

### No Rate Limiting in Application Code
**What this means:** The NFRs define rate limits (10 POST/minute per IP, 100 GET/minute per IP), but these are not implemented in the application. They require an external reverse proxy or API gateway (nginx, Cloudflare, AWS API Gateway).

**Impact:** Running this application directly on a public internet port without a reverse proxy exposes it to abuse and DoS from high-volume URL creation or redirect traffic.

---

### SQLite Is Not Production-Ready for High Concurrency
**What this means:** SQLite supports limited concurrent writers. Under high load, write operations (POST /urls, redirect analytics update) will queue behind each other.

**Impact:** Not suitable for high-throughput production use. Switch to PostgreSQL via `DATABASE_URL=postgresql://...` for concurrent write workloads.

---

### No URL Reachability Validation
**What this means:** The service validates URL *format* but does not verify that the URL is *reachable*. A client can shorten `https://nonexistent-domain-xyz-123.com/path` and the service will accept it.

**Impact:** Short URLs may redirect to dead links with no indication at creation time.

---

## Security Limitations

### No CSP Headers on `/docs` Endpoint
FastAPI's auto-generated `/docs` (Swagger UI) does not include Content-Security-Policy headers. This is a low-severity gap for production deployments.

### No Recursive Short URL Detection
The blocklist blocks known short-URL services (`bit.ly`, `tinyurl.com`) to prevent chaining, but this is heuristic-based — new short URL services are not automatically blocked.

### No Click-Time Malware Scanning
URLs are checked against a static blocklist at creation time. A URL that becomes malicious after shortening (compromised domain, URL redirected to malware) is not re-checked on each click.

---

## Scope Limitations

This project is an **assignment implementation**, not a production service. It is:

- Not deployed (no CI/CD, no monitoring, no alerting)
- Not hardened for production (no TLS enforcement in-app, no CORS configuration, no production-grade logging)
- Not audited beyond the self-critique loop documented in `docs/self-critique-log.md`

Claims of "production-ready" are explicitly **not made**. See `SECURITY.md` for known security limitations.
