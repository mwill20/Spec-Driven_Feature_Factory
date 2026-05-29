# Test suite — URL validation (REQ-SHORT-005) + utility unit tests
# Generated from: prompts/test-generator.yaml
# Covers: SCN-005, SCN-006, SCN-007, SCN-010 + unit tests for utils.py

import pytest

from src.utils import (
    generate_short_code,
    hash_url,
    validate_url,
    UrlValidationError,
    CODE_LENGTH,
    CODE_ALPHABET,
)


# ─── Unit tests for utils.py ──────────────────────────────────────────────────

class TestGenerateShortCode:
    """REQ-SHORT-001"""

    def test_code_is_correct_length(self):
        """
        REQ-ID: REQ-SHORT-001 | Type: unit
        Generated code must be exactly 6 characters.
        """
        assert len(generate_short_code()) == CODE_LENGTH

    def test_code_uses_only_allowed_characters(self):
        """
        REQ-ID: REQ-SHORT-001 | Type: unit
        Code characters must all be in [a-zA-Z0-9].
        """
        code = generate_short_code()
        assert all(c in CODE_ALPHABET for c in code)

    def test_codes_are_unique_across_calls(self):
        """
        REQ-ID: REQ-SHORT-001 | Type: unit | edge_case
        100 sequential calls must not produce a collision (statistical guarantee).
        """
        codes = {generate_short_code() for _ in range(100)}
        assert len(codes) == 100, "Unexpected collision in 100 generated codes"


class TestHashUrl:
    """REQ-SHORT-005"""

    def test_same_url_produces_same_hash(self):
        """
        REQ-ID: REQ-SHORT-005 | Type: unit
        Idempotency: hashing the same URL twice must yield identical digest.
        """
        url = "https://www.example.com/path"
        assert hash_url(url) == hash_url(url)

    def test_different_urls_produce_different_hashes(self):
        """
        REQ-ID: REQ-SHORT-005 | Type: unit
        Two distinct URLs must produce distinct hashes.
        """
        h1 = hash_url("https://www.example.com/a")
        h2 = hash_url("https://www.example.com/b")
        assert h1 != h2

    def test_hash_is_64_hex_chars(self):
        """
        REQ-ID: REQ-SHORT-005 | Type: unit
        SHA-256 digest must be 64 hex characters.
        """
        h = hash_url("https://www.example.com")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestValidateUrl:
    """REQ-SHORT-005"""

    def test_valid_http_url_passes(self):
        """
        REQ-ID: REQ-SHORT-005 | Type: unit
        Standard HTTP URL must pass validation without error.
        """
        result = validate_url("http://www.example.com/page")
        assert result == "http://www.example.com/page"

    def test_valid_https_url_passes(self):
        """
        REQ-ID: REQ-SHORT-005 | Type: unit
        Standard HTTPS URL must pass validation.
        """
        result = validate_url("https://www.example.com/secure")
        assert result == "https://www.example.com/secure"

    def test_ftp_scheme_raises_validation_error(self):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-006 | Type: unit
        FTP URLs must raise UrlValidationError with INVALID_SCHEME code.
        """
        with pytest.raises(UrlValidationError) as exc_info:
            validate_url("ftp://files.example.com/data")
        assert exc_info.value.error_code == "INVALID_SCHEME"

    def test_plain_text_raises_validation_error(self):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-005 | Type: unit
        Non-URL strings must raise UrlValidationError.
        """
        with pytest.raises(UrlValidationError):
            validate_url("this is not a url at all")

    def test_private_ip_192_168_raises_validation_error(self):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-010 | Type: security
        192.168.x.x URLs must be rejected to prevent SSRF.
        """
        with pytest.raises(UrlValidationError) as exc_info:
            validate_url("http://192.168.1.1/admin")
        assert exc_info.value.error_code == "PRIVATE_IP"

    def test_private_ip_10_x_raises_validation_error(self):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-010 | Type: security
        10.x.x.x URLs must be rejected to prevent SSRF.
        """
        with pytest.raises(UrlValidationError) as exc_info:
            validate_url("http://10.0.0.1/internal")
        assert exc_info.value.error_code == "PRIVATE_IP"

    def test_localhost_raises_validation_error(self):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-010 | Type: security
        Localhost (127.0.0.1) must be rejected.
        """
        with pytest.raises(UrlValidationError) as exc_info:
            validate_url("http://127.0.0.1/")
        assert exc_info.value.error_code == "PRIVATE_IP"

    def test_blocked_domain_raises_validation_error(self):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-007 | Type: error_case
        A URL whose domain is on the blocklist must raise UrlValidationError with BLOCKED code.
        """
        with pytest.raises(UrlValidationError) as exc_info:
            validate_url(
                "https://malware.example.com/payload",
                blocked_domains=["malware.example.com"],
            )
        assert exc_info.value.error_code == "BLOCKED"

    def test_subdomain_of_blocked_domain_also_blocked(self):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-007 | Type: edge_case
        Subdomains of a blocked domain must also be blocked.
        """
        with pytest.raises(UrlValidationError) as exc_info:
            validate_url(
                "https://sub.malware.example.com/payload",
                blocked_domains=["malware.example.com"],
            )
        assert exc_info.value.error_code == "BLOCKED"

    def test_url_exceeding_max_length_raises_error(self):
        """
        REQ-ID: REQ-SHORT-005 | Type: edge_case
        URLs longer than 2048 characters must be rejected.
        """
        long_url = "https://www.example.com/" + "a" * 2048
        with pytest.raises(UrlValidationError):
            validate_url(long_url)
