# Test suite — Redirect and 404 handling (GET /{code})
# Generated from: prompts/test-generator.yaml
# Covers: SCN-002 (redirect), SCN-009 (404), SCN-004 (expired)

import pytest
from datetime import datetime, timezone, timedelta

from tests.conftest import VALID_URL


class TestRedirect:
    """REQ-SHORT-002, REQ-SHORT-004, REQ-SHORT-006"""

    def _create_url(self, client, url: str, expires_at=None) -> str:
        payload = {"url": url}
        if expires_at:
            payload["expires_at"] = expires_at
        r = client.post("/urls", json=payload)
        assert r.status_code in (200, 201)
        return r.json()["short_code"]

    def test_valid_short_code_returns_302_redirect(self, client):
        """
        REQ-ID: REQ-SHORT-002 | Scenario: SCN-002 | Type: happy_path
        GET /{valid_code} must return 302 with Location header pointing to original URL.
        """
        code = self._create_url(client, VALID_URL)

        response = client.get(f"/{code}", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == VALID_URL

    def test_nonexistent_code_returns_404(self, client):
        """
        REQ-ID: REQ-SHORT-002, REQ-SHORT-006 | Scenario: SCN-009 | Type: error_case
        GET /{nonexistent_code} must return 404 with structured error body.
        """
        response = client.get("/zzz999", follow_redirects=False)

        assert response.status_code == 404

    def test_expired_url_returns_410(self, client):
        """
        REQ-ID: REQ-SHORT-004, REQ-SHORT-002 | Scenario: SCN-004 | Type: error_case
        GET /{expired_code} must return 410 Gone when expires_at is in the past.
        """
        past = "2020-01-01T00:00:00Z"
        code = self._create_url(
            client, "https://www.example.com/expired-promo", expires_at=past
        )

        response = client.get(f"/{code}", follow_redirects=False)

        assert response.status_code == 410

    def test_future_expiry_allows_redirect(self, client):
        """
        REQ-ID: REQ-SHORT-004 | Scenario: SCN-004 context | Type: happy_path
        A URL with a future expires_at must still redirect normally.
        """
        future = "2099-12-31T23:59:59Z"
        code = self._create_url(
            client, "https://www.example.com/future-promo", expires_at=future
        )

        response = client.get(f"/{code}", follow_redirects=False)

        assert response.status_code == 302
