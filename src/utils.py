# REQ-SHORT-001, REQ-SHORT-005
# URL validation and short-code generation utilities.

import hashlib
import ipaddress
import random
import re
import string
from urllib.parse import urlparse

# REQ-SHORT-001: 6-char base-62 alphabet — 62^6 ≈ 56 billion possible codes
CODE_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6

# REQ-SHORT-005: private/reserved IP ranges to block SSRF
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def generate_short_code() -> str:
    """Generate a cryptographically random 6-character alphanumeric code.

    REQ-SHORT-001: unique alphanumeric short codes of exactly 6 characters.
    Uses secrets-quality randomness via random.SystemRandom.
    """
    rng = random.SystemRandom()
    return "".join(rng.choices(CODE_ALPHABET, k=CODE_LENGTH))


def hash_url(url: str) -> str:
    """Return SHA-256 hex digest of the normalized URL.

    REQ-SHORT-005: enables O(1) duplicate detection without full-text scan.
    """
    normalized = url.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class UrlValidationError(ValueError):
    def __init__(self, message: str, error_code: str = "INVALID_URL"):
        self.error_code = error_code
        super().__init__(message)


def validate_url(url: str, blocked_domains: list[str] | None = None) -> str:
    """Validate and return the normalized URL.

    REQ-SHORT-005: rejects:
      - non-HTTP/HTTPS schemes
      - malformed URLs
      - private/reserved IPs (SSRF prevention)
      - domains on the configurable blocklist

    Returns the stripped, validated URL string.
    Raises UrlValidationError with an error_code for callers to map to HTTP status.
    """
    url = url.strip()

    if len(url) > 2048:
        raise UrlValidationError("URL exceeds maximum length of 2048 characters")

    try:
        parsed = urlparse(url)
    except Exception:
        raise UrlValidationError(f"URL could not be parsed: {url!r}")

    # REQ-SHORT-005a: scheme must be http or https
    if parsed.scheme not in ("http", "https"):
        raise UrlValidationError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed.",
            error_code="INVALID_SCHEME",
        )

    # Must have a netloc (host)
    if not parsed.netloc:
        raise UrlValidationError("URL must include a host", error_code="MISSING_HOST")

    hostname = parsed.hostname or ""

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

    return url
