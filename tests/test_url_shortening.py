# Test suite — URL Shortening (POST /urls)
# Generated from: prompts/test-generator.yaml
# Covers: SCN-001 (happy path), SCN-008 (idempotency), SCN-005, SCN-006, SCN-007 (error paths)

import re

import pytest

from tests.conftest import VALID_URL, ANOTHER_VALID_URL

CODE_PATTERN = re.compile(r"^[a-zA-Z0-9]{6}$")


class TestUrlShortening:
    """REQ-SHORT-001, REQ-SHORT-005, REQ-SHORT-006"""

    def test_shorten_valid_url_returns_201(self, client):
        """
        REQ-ID: REQ-SHORT-001 | Scenario: SCN-001 | Type: happy_path
        Successfully shorten a valid URL — expects 201 Created with a 6-char short_code.
        """
        response = client.post("/urls", json={"url": VALID_URL})

        assert response.status_code == 201
        data = response.json()
        assert "short_code" in data
        assert CODE_PATTERN.match(data["short_code"]), (
            f"short_code '{data['short_code']}' does not match 6-char alphanumeric pattern"
        )
        assert data["url"] == VALID_URL
        assert data["short_code"] in data["short_url"]

    def test_shorten_url_response_contains_all_required_fields(self, client):
        """
        REQ-ID: REQ-SHORT-001, REQ-SHORT-006 | Scenario: SCN-001 | Type: happy_path
        Response schema validation — all required fields present (JSON schema enforcement).
        """
        response = client.post("/urls", json={"url": ANOTHER_VALID_URL})
        data = response.json()

        required_fields = {"short_code", "short_url", "url", "created_at"}
        assert required_fields.issubset(data.keys()), (
            f"Missing fields: {required_fields - data.keys()}"
        )

    def test_idempotent_submission_returns_200_with_same_code(self, client):
        """
        REQ-ID: REQ-SHORT-001, REQ-SHORT-005 | Scenario: SCN-008 | Type: edge_case
        Submitting the same URL twice returns the existing short_code and HTTP 200.
        """
        first = client.post("/urls", json={"url": VALID_URL})
        assert first.status_code == 201
        first_code = first.json()["short_code"]

        second = client.post("/urls", json={"url": VALID_URL})
        assert second.status_code == 200
        assert second.json()["short_code"] == first_code
        assert second.json()["already_exists"] is True

    def test_two_different_urls_get_different_codes(self, client):
        """
        REQ-ID: REQ-SHORT-001 | Scenario: SCN-001 | Type: happy_path
        Distinct URLs must produce distinct short codes.
        """
        r1 = client.post("/urls", json={"url": VALID_URL})
        r2 = client.post("/urls", json={"url": ANOTHER_VALID_URL})

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["short_code"] != r2.json()["short_code"]

    def test_reject_invalid_url_format_returns_422(self, client):
        """
        REQ-ID: REQ-SHORT-005, REQ-SHORT-006 | Scenario: SCN-005 | Type: error_case
        A non-URL string must be rejected with 422 Unprocessable Entity.
        """
        response = client.post("/urls", json={"url": "not-a-url"})
        assert response.status_code == 422

    def test_reject_ftp_scheme_returns_422(self, client):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-006 | Type: error_case
        FTP URLs must be rejected — only http/https are supported.
        """
        response = client.post("/urls", json={"url": "ftp://files.example.com/data"})
        assert response.status_code == 422

    def test_reject_file_scheme_returns_422(self, client):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-006 | Type: error_case
        file:// URIs must be rejected to prevent local file disclosure.
        """
        response = client.post("/urls", json={"url": "file:///etc/passwd"})
        assert response.status_code == 422

    def test_reject_blocked_domain_returns_400(self, client):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-007 | Type: error_case
        URLs on the malicious domain blocklist must return 400 with BLOCKED error.
        """
        response = client.post(
            "/urls", json={"url": "https://malware.example.com/payload"}
        )
        assert response.status_code == 400

    def test_reject_private_ip_returns_422(self, client):
        """
        REQ-ID: REQ-SHORT-005 | Scenario: SCN-010 | Type: error_case (security)
        SSRF prevention: private/reserved IP addresses must be rejected with 422.
        """
        for private_url in [
            "http://192.168.1.1/admin",
            "http://10.0.0.1/internal",
            "http://127.0.0.1/localhost",
        ]:
            response = client.post("/urls", json={"url": private_url})
            assert response.status_code == 422, (
                f"Expected 422 for {private_url}, got {response.status_code}"
            )

    def test_url_with_expiry_is_accepted(self, client):
        """
        REQ-ID: REQ-SHORT-004 | Scenario: SCN-004 context | Type: happy_path
        POST /urls with a future expires_at must succeed with 201.
        """
        response = client.post(
            "/urls",
            json={
                "url": "https://www.example.com/timed-offer",
                "expires_at": "2099-12-31T23:59:59Z",
            },
        )
        assert response.status_code == 201
        assert response.json()["expires_at"] is not None
