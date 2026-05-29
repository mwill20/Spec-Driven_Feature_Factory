# 🎓 Lesson 03: The Steel Door — SSRF Prevention and URL Validation Security

## 🛡️ Welcome Back, Security Analyst!

You know this scenario from your FortiEDR work: a process on a workstation makes an unexpected outbound connection to `192.168.1.1` — an internal network address it has no business reaching. That's lateral movement. 🔍 Today we're exploring `src/utils.py` — the "steel door" that prevents a URL shortener from being weaponized for exactly that kind of attack. This is the most security-critical file in the project, and it contains one of the most instructive bugs: a Python exception hierarchy trap that silently disabled SSRF protection until the self-critique cycle caught it.

---

## 🎯 Learning Objectives

By the end of this lesson you will be able to:

- Define SSRF (Server-Side Request Forgery) and explain why URL shorteners are a natural SSRF vector
- Read the `validate_url()` function and identify every security check it performs
- Explain the Python `try/except/else` pattern and why it's required here
- Describe how exception inheritance creates silent security bypasses
- Trace the difference between an app-level blocklist and an IP-range blocklist

**Time estimate:** 40 minutes | **Prerequisites:** Lesson 01

---

## 🧠 What This Component Does — Plain English

`src/utils.py` is the gatekeeper that runs before any URL is stored in the database. It answers one question: "Is this URL safe to shorten?" If the answer is no, it raises `UrlValidationError` with a machine-readable error code. The caller (the router in `src/routers/urls.py`) maps that error code to the correct HTTP status — 422 for invalid format, 400 for blocked domain.

The file has three distinct jobs:

1. **Code generation** (`generate_short_code`): create cryptographically random 6-char codes using `random.SystemRandom()` (OS-level randomness, not Python's default predictable PRNG)
2. **URL hashing** (`hash_url`): create a SHA-256 fingerprint for deduplication
3. **URL validation** (`validate_url`): enforce scheme, format, private IP, and blocklist rules

**Real-world analogy:** Your VirusTotal API calls validate IOCs against known malicious signatures. Your internal IP range blocklist prevents analysts from accidentally enriching internal infrastructure against external threat intel services. `validate_url()` does both: it validates the format (is this actually a URL?) and checks it against a blocklist (is this a known bad domain?). The SSRF check is the equivalent of your SIEM alert that fires when an internal service calls an RFC 1918 address it shouldn't be reaching.

---

## 🗺️ Where This Fits in the System

```
🌐 POST /urls body {url: "..."}
        ↓
📋 FastAPI Router — shorten_url()
        ↓
🚪 validate_url() in src/utils.py   ← (THIS LESSON — THE STEEL DOOR)
   ├─ Scheme check (http/https only)
   ├─ Format check (parseable URI with netloc)
   ├─ Private IP check (SSRF prevention)
   └─ Blocklist check (known malicious domains)
        ↓ (only if validation passes)
📦 CRUD Layer — create_short_url()
        ↓
💾 Database
```

If `validate_url()` is removed or its checks are disabled, the service becomes an SSRF amplification tool: an attacker submits `http://internal-database:5432/` as a URL, and the shortener creates a public short link that, when clicked by an admin, probes the internal network.

---

## 🔑 Key Concepts

### SSRF (Server-Side Request Forgery)

SSRF is OWASP A10 (2021). In an SSRF attack, an attacker tricks a server into making HTTP requests to unintended destinations — typically internal services the attacker cannot reach directly. A URL shortener is a particularly dangerous SSRF surface because:

1. The service doesn't currently fetch the URL (it just stores it) — but any future feature that "previews" the destination would trigger the SSRF
2. The short URL itself becomes a social engineering tool: `https://short.example.com/xK3mPq` looks safe; the destination `http://192.168.1.1/admin` does not. Clicking the short link from an admin workstation could bypass firewall rules that block direct access to the internal address

The fix is to validate the URL at submission time, before it's stored, so the attack surface never exists.

### Python Exception Inheritance and the Silent Bypass

`UrlValidationError` inherits from `ValueError`:

```python
class UrlValidationError(ValueError):
    def __init__(self, message: str, error_code: str = "INVALID_URL"):
        self.error_code = error_code
        super().__init__(message)
```

This inheritance exists so callers can catch `UrlValidationError` specifically (precise handling) or `ValueError` broadly (general error handling). But it creates a trap: if you raise `UrlValidationError` inside a `try` block that has `except ValueError`, Python catches it — because `UrlValidationError` IS a `ValueError`. The security check silently fails.

This is exactly what happened in the first version of `validate_url()`. The SSRF check raised `UrlValidationError` inside a `try/except ValueError` block, and the `except` caught it and did nothing. The test `test_reject_private_ip_returns_422` returned 200 instead of 422.

### try/except/else

Python's `try/except/else` pattern separates "the operation failed" from "the operation succeeded but the result needs further handling":

```python
try:
    addr = ipaddress.ip_address(hostname)   # attempt the conversion
except ValueError:
    pass                                     # hostname isn't an IP — that's fine
else:
    for network in _PRIVATE_NETWORKS:       # only runs if try succeeded
        if addr in network:
            raise UrlValidationError(...)    # safely raises WITHOUT being caught above
```

The `else` block runs only when the `try` block completes without any exception. Because `UrlValidationError` is raised *inside the `else` block*, it is never in scope of the `except ValueError` above — it propagates normally to the caller.

### Configurable Blocklist vs. Hardcoded IP Ranges

The SSRF protection uses two different mechanisms for two different threat models:

- **IP range blocklist (hardcoded):** Private RFC 1918 addresses and localhost are *universally* dangerous to accept. They never change. Hardcoding them is correct.
- **Domain blocklist (database-driven):** Malicious domains change daily. The blocklist is seeded from `src/main.py` at startup and can be extended at runtime by inserting rows into the `blocklist` table. This is configurable by operators without code changes.

---

## 📝 Code Walkthrough

### The SSRF Private IP Check

```python
# src/utils.py — Lines 87–99
    # REQ-SHORT-005c (extended): block private/reserved IPs — SSRF prevention
    # Use try/else to avoid catching our own UrlValidationError (which inherits ValueError).
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        pass  # Not an IP literal — it's a hostname, continue to blocklist check
    else:
        for network in _PRIVATE_NETWORKS:
            if addr in network:
                raise UrlValidationError(
                    f"URL resolves to a private or reserved IP address: {hostname}",
                    error_code="PRIVATE_IP",
                )
```

**The bug that was here before the fix (Cycle 1 — FIND-001):**

```python
# BROKEN — do not use this pattern
try:
    addr = ipaddress.ip_address(hostname)
    for network in _PRIVATE_NETWORKS:
        if addr in network:
            raise UrlValidationError(...)   # <-- UrlValidationError IS a ValueError
except ValueError:
    pass  # <-- catches BOTH "not an IP" AND "is a private IP"
```

In the broken version, submitting `http://192.168.1.1/admin` produced:
1. `hostname = "192.168.1.1"`
2. `addr = ipaddress.ip_address("192.168.1.1")` — succeeds
3. `addr in ipaddress.ip_network("192.168.0.0/16")` — True
4. `raise UrlValidationError(...)` — raised but caught by `except ValueError` immediately above
5. Function continues, returns the URL as valid

**The severity:** This is a silent security bypass — no exception, no log, no indication of failure. The SSRF check appeared to work in code review but did nothing. It was only caught because the test `test_reject_private_ip_returns_422` expected 422 and got 200.

### The Private Network Definitions

```python
# src/utils.py — Lines 16–24
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]
```

**Why these specific ranges:**

| Range | Name | Why blocked |
|-------|------|------------|
| `10.0.0.0/8` | RFC 1918 Class A | Internal corporate networks |
| `172.16.0.0/12` | RFC 1918 Class B | Internal networks (172.16 – 172.31) |
| `192.168.0.0/16` | RFC 1918 Class C | Home/office internal networks |
| `127.0.0.0/8` | Loopback | Localhost — would probe the server itself |
| `169.254.0.0/16` | Link-local (APIPA) | AWS metadata service (`169.254.169.254`) — critical SSRF target |
| `::1/128` | IPv6 loopback | IPv6 localhost |
| `fc00::/7` | IPv6 unique-local | IPv6 equivalent of RFC 1918 |

> ⚠️ **Important gap documented in self-critique log:** This check only works for URLs where the hostname is a literal IP address (e.g., `http://192.168.1.1/admin`). A URL like `http://internal-db.corp.local/` would pass validation because `internal-db.corp.local` is a hostname, not an IP literal — `ipaddress.ip_address()` raises `ValueError`, which means the `else` block never runs. DNS resolution at validation time would be required to close this gap, but it introduces latency and complexity. This is documented as an accepted risk in `docs/self-critique-log.md`.

### The Blocklist Check

```python
# src/utils.py — Lines 101–111
    # REQ-SHORT-005c: check configurable blocklist
    if blocked_domains:
        domain_lower = hostname.lower()
        for blocked in blocked_domains:
            if domain_lower == blocked.lower() or domain_lower.endswith(
                "." + blocked.lower()
            ):
                raise UrlValidationError(
                    f"Domain '{hostname}' is on the blocklist",
                    error_code="BLOCKED",
                )
```

**The subdomain check:** `domain_lower.endswith("." + blocked.lower())` ensures that blocking `malware.example.com` also blocks `sub.malware.example.com`. Without the dot prefix (`"." + blocked`), the check would also match `notmalware.example.com` — a false positive. The dot ensures we match on the subdomain boundary, not a substring.

**Design pattern:** The blocklist is passed as a parameter (`blocked_domains: list[str] | None = None`) rather than fetched inside `validate_url()`. This keeps the function pure and testable: unit tests can pass any blocklist directly without a database. Integration tests pass the real blocklist from the database. The router is responsible for fetching the blocklist from the database and passing it to the function.

### The Code Generator

```python
# src/utils.py — Lines 27–34
def generate_short_code() -> str:
    """Generate a cryptographically random 6-character alphanumeric code.

    REQ-SHORT-001: unique alphanumeric short codes of exactly 6 characters.
    Uses secrets-quality randomness via random.SystemRandom.
    """
    rng = random.SystemRandom()
    return "".join(rng.choices(CODE_ALPHABET, k=CODE_LENGTH))
```

`random.SystemRandom()` uses the OS's CSPRNG (cryptographically secure pseudo-random number generator) — on Linux/macOS this is `/dev/urandom`, on Windows it's `CryptGenRandom`. Python's default `random` module uses the Mersenne Twister algorithm, which is fast but predictable if an attacker can observe enough outputs. For short codes that are effectively access credentials (knowing the code gives you the redirect target), CSPRNG-quality randomness matters.

---

## 🧪 Hands-On Exercises

> Activate the virtual environment: `.\.venv\Scripts\Activate.ps1`

### 🔬 Exercise 1: Test the SSRF Protection Directly

This exercise proves the private IP check works at the function level.

```powershell
python -c "
from src.utils import validate_url, UrlValidationError

test_cases = [
    ('http://192.168.1.1/admin', 'PRIVATE_IP'),
    ('http://10.0.0.1/internal', 'PRIVATE_IP'),
    ('http://127.0.0.1/', 'PRIVATE_IP'),
    ('http://169.254.169.254/latest/meta-data/', 'PRIVATE_IP'),
    ('ftp://files.example.com/', 'INVALID_SCHEME'),
    ('not-a-url', 'INVALID_SCHEME'),
]

for url, expected_code in test_cases:
    try:
        validate_url(url)
        print(f'FAIL: {url!r} should have been rejected')
    except UrlValidationError as e:
        status = 'PASS' if e.error_code == expected_code else f'WRONG CODE: got {e.error_code}'
        print(f'{status}: {url!r} → {e.error_code}')
"
```

📊 **Expected output:**
```
PASS: 'http://192.168.1.1/admin' → PRIVATE_IP
PASS: 'http://10.0.0.1/internal' → PRIVATE_IP
PASS: 'http://127.0.0.1/' → PRIVATE_IP
PASS: 'http://169.254.169.254/latest/meta-data/' → PRIVATE_IP
PASS: 'ftp://files.example.com/' → INVALID_SCHEME
PASS: 'not-a-url' → INVALID_SCHEME
```

✅ **You succeeded if:** All 6 lines say PASS and the error codes match exactly.

---

### 🔬 Exercise 2: Demonstrate the Exception Inheritance Trap

This exercise recreates the FIND-001 bug to show exactly why `try/except/else` was necessary.

```powershell
python -c "
import ipaddress

class MyValidationError(ValueError):
    pass

# BROKEN pattern — simulates the original bug
def broken_check(hostname):
    try:
        addr = ipaddress.ip_address(hostname)
        if addr in ipaddress.ip_network('192.168.0.0/16'):
            raise MyValidationError('PRIVATE IP DETECTED')
        return 'safe'
    except ValueError:
        return 'not-an-ip-hostname'

# FIXED pattern — simulates the corrected code
def fixed_check(hostname):
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        return 'not-an-ip-hostname'
    else:
        if addr in ipaddress.ip_network('192.168.0.0/16'):
            raise MyValidationError('PRIVATE IP DETECTED')
    return 'safe'

# Test both
print('Broken check on 192.168.1.1:', broken_check('192.168.1.1'))  # Should detect, returns 'safe' WRONG
print('Fixed check on 192.168.1.1:', end=' ')
try:
    result = fixed_check('192.168.1.1')
    print(result)
except MyValidationError as e:
    print('BLOCKED:', e)  # Correct

print('Broken check on example.com:', broken_check('example.com'))  # Correct
print('Fixed check on example.com:', fixed_check('example.com'))   # Correct
"
```

📊 **Expected output:**
```
Broken check on 192.168.1.1: not-an-ip-hostname
Fixed check on 192.168.1.1: BLOCKED: PRIVATE IP DETECTED
Broken check on example.com: not-an-ip-hostname
Fixed check on example.com: not-an-ip-hostname
```

✅ **You succeeded if:** The broken check says `not-an-ip-hostname` for `192.168.1.1` (wrong — it silently passed), while the fixed check raises `BLOCKED` (correct). This is FIND-001 reproduced in 20 lines.

---

### 🔬 Exercise 3: Run Only Security Tests

This exercise runs the subset of tests that verify security controls.

```powershell
python -m pytest tests/test_validation.py -v -k "private or blocked or ssrf or scheme" --tb=short
```

📊 **Expected output:**
```
tests/test_validation.py::TestValidateUrl::test_ftp_scheme_raises_validation_error PASSED
tests/test_validation.py::TestValidateUrl::test_private_ip_192_168_raises_validation_error PASSED
tests/test_validation.py::TestValidateUrl::test_private_ip_10_x_raises_validation_error PASSED
tests/test_validation.py::TestValidateUrl::test_localhost_raises_validation_error PASSED
tests/test_validation.py::TestValidateUrl::test_blocked_domain_raises_validation_error PASSED
tests/test_validation.py::TestValidateUrl::test_subdomain_of_blocked_domain_also_blocked PASSED

6 passed in X.XXs
```

✅ **You succeeded if:** All 6 security-focused tests pass. If any fail, the SSRF protection is broken.

---

### 🔬 Exercise 4 (Optional): Test the AWS Metadata Service Endpoint Specifically

The `169.254.169.254` address is the AWS EC2 instance metadata service — one of the most commonly targeted SSRF endpoints in cloud environments. This exercise verifies it's blocked.

```powershell
python -c "
from src.utils import validate_url, UrlValidationError
try:
    validate_url('http://169.254.169.254/latest/meta-data/iam/security-credentials/')
    print('CRITICAL: AWS metadata endpoint was NOT blocked!')
except UrlValidationError as e:
    print('PASS: AWS metadata endpoint blocked:', e.error_code)
    print('Message:', str(e))
"
```

📊 **Expected output:**
```
PASS: AWS metadata endpoint blocked: PRIVATE_IP
Message: URL resolves to a private or reserved IP address: 169.254.169.254
```

✅ **You succeeded if:** The endpoint is blocked with `PRIVATE_IP`. An unblocked AWS metadata service is the most common cloud SSRF exploitation path — it provides IAM credentials to anyone who can make the server fetch that URL.

---

## 📚 Interview Preparation

### Q: What is SSRF, and why is a URL shortener a high-risk SSRF surface?

**A:** SSRF (Server-Side Request Forgery, OWASP A10) is an attack where an attacker tricks a server into making requests to unintended destinations — typically internal services not accessible from the internet. A URL shortener is high-risk for SSRF because it stores user-supplied URLs and may later fetch them (for link previews, click verification, or metadata display). Even if the current implementation only stores URLs without fetching them, any future "preview" feature would immediately expose the SSRF surface. Blocking at submission time means the attack surface never exists, regardless of future features. Blocking at fetch time means every future developer must remember to add the check.

*Why this answer works:* It explains the threat, identifies why this specific component is high-risk, and articulates why prevention at the earliest possible boundary is the correct design.

---

### Q: Walk me through the exception hierarchy bug in the original SSRF check. How was it caught?

**A:** `UrlValidationError` inherits from `ValueError`. The original code raised `UrlValidationError` inside a `try/except ValueError` block. Because `UrlValidationError` is a subclass of `ValueError`, Python's exception matching caught it immediately — the exception never propagated to the caller. A private IP address like `192.168.1.1` would pass validation silently, and the SSRF protection was completely disabled despite appearing correct in code review. It was caught by the test `test_reject_private_ip_returns_422`, which expected HTTP 422 and received HTTP 200. The fix was to restructure the code using `try/except/else` — the `else` block runs only when no exception occurred in `try`, and any exceptions raised in `else` are not caught by the `except ValueError` above.

*Why this answer works:* It demonstrates understanding of Python exception semantics at a level most candidates don't reach, and it shows that testing security controls is not optional.

---

### Q: Why does blocking `malware.example.com` also need to block `sub.malware.example.com`? How is this implemented?

**A:** Subdomains are controlled by the same domain owner. If `malware.example.com` is blocked because its operator is known to distribute malware, any subdomain (`sub.malware.example.com`, `cdn.malware.example.com`, `download.malware.example.com`) is equally untrusted — the same operator controls all of them. The check is: `domain_lower.endswith("." + blocked.lower())`. The dot prefix is critical: without it, `"somemalware.example.com".endswith("malware.example.com")` would return `True` (false positive). With the dot: `"somemalware.example.com".endswith(".malware.example.com")` returns `False` (correct), while `"sub.malware.example.com".endswith(".malware.example.com")` returns `True` (correct).

*Why this answer works:* It shows awareness of subdomain trust inheritance and knowledge of how to implement a correct boundary check.

---

## ✅ Key Takeaways

- SSRF prevention must happen at the earliest boundary — at URL submission, not at URL fetch time — because blocking later requires every downstream consumer to implement the check
- Python exception inheritance creates silent security bypasses when a security-raising exception is a subclass of the exception being caught — `try/except/else` separates the two concerns cleanly
- Private IP ranges (RFC 1918, loopback, link-local including `169.254.169.254`) must be blocked as literals; DNS hostname resolution is a harder problem with latency tradeoffs
- The subdomain blocklist check requires a dot prefix (`"." + blocked_domain`) to prevent false positives on shared suffixes
- `random.SystemRandom()` provides CSPRNG-quality randomness; Python's default `random` module does not — use `SystemRandom` whenever randomness has a security implication

---

## 📋 Quick Reference Card

| Item | Value |
|------|-------|
| File | `src/utils.py` |
| Entry points | `generate_short_code()`, `hash_url()`, `validate_url()` |
| Input | URL string, optional blocked domain list |
| Output | Validated URL string, or raises `UrlValidationError` |
| Error codes | `INVALID_URL`, `INVALID_SCHEME`, `MISSING_HOST`, `PRIVATE_IP`, `BLOCKED` |
| SSRF private ranges | RFC 1918 (10/8, 172.16/12, 192.168/16), loopback (127/8), link-local (169.254/16), IPv6 |
| Key pattern | `try/except/else` to prevent exception inheritance swallowing |
| Code alphabet | `string.ascii_letters + string.digits` (62 chars, 62^6 ≈ 56B codes) |
| Hash algorithm | SHA-256 of lowercased+stripped URL |
| RNG | `random.SystemRandom()` (OS CSPRNG) |
| Test file | `tests/test_validation.py`, `tests/test_url_shortening.py` |

---

## 📌 Implemented vs. Recommended

### What This Project Implements ✅
- Scheme validation (http/https only) — `validate_url()` lines 74–79
- Private IP range blocking (IPv4 + IPv6) — `validate_url()` lines 87–99
- Configurable domain blocklist with subdomain matching — `validate_url()` lines 101–111
- CSPRNG code generation — `generate_short_code()` using `SystemRandom`
- SHA-256 URL fingerprinting — `hash_url()` with lowercase normalization

### General Best Practices — Not Implemented Here
- **DNS resolution at validation time** — resolving hostnames to IPs to catch `http://internal-db.corp.local/` — `Recommended (not implemented here)` — adds latency and complexity; typically done at the infrastructure layer (e.g., egress firewall rules)
- **URL scheme allow-list in config** — storing allowed schemes in an environment variable rather than hardcoding `("http", "https")` — `Recommended (not implemented here)` for multi-environment deployments
- **SSRF detection at the CDN/proxy layer** — egress filtering to block requests to RFC 1918 ranges at the network level — `Recommended (not implemented here)` — defense in depth: app layer + network layer

---

## 🚀 You've Completed the Core Curriculum!

You've now traced the full lifecycle of a URL through this service: from the spec that defined what "valid" means (Lesson 01), through the database layer that stores it (Lesson 02), through the security gate that protects the service (Lesson 03).

**The complete picture:**

```
PM says "shorten URLs" 
  → spec says WHAT (REQ-SHORT-005: reject private IPs) 
    → utils.py enforces HOW (try/except/else, IP range check) 
      → test proves it WORKS (test_reject_private_ip_returns_422)
        → self-critique caught the BUG (FIND-001: silent bypass)
          → fix makes it CORRECT (46/46 passing)
```

**Optional deeper dive:** Read OWASP's SSRF Prevention Cheat Sheet (online) — it covers DNS rebinding attacks, which are the next level of SSRF sophistication beyond what this project implements.

**Modification challenge:** Add `0.0.0.0` to the private IP blocklist. Research why `http://0.0.0.0/` is a valid SSRF vector on Linux systems (hint: it resolves to localhost on some OS configurations). Add it to `_PRIVATE_NETWORKS` in `src/utils.py` and write a new test `test_zero_ip_raises_validation_error` in `tests/test_validation.py`.

*Remember: a security check that fails silently is worse than no check at all — it creates false confidence.* 🛡️
