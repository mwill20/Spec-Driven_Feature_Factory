# Test suite — URL expiry (REQ-SHORT-004)
# Generated from: prompts/test-generator.yaml
# Covers: SCN-004 (expired returns 410), future expiry allows redirect

import pytest


class TestExpiry:
    """REQ-SHORT-004"""

    def test_url_without_expiry_never_expires(self, client):
        """
        REQ-ID: REQ-SHORT-004 | Scenario: SCN-004 context | Type: happy_path
        POST /urls without expires_at must create a URL that redirects indefinitely.
        """
        r = client.post("/urls", json={"url": "https://www.example.com/no-expiry"})
        assert r.status_code == 201
        assert r.json()["expires_at"] is None

        code = r.json()["short_code"]
        redirect = client.get(f"/{code}", follow_redirects=False)
        assert redirect.status_code == 302

    def test_past_expiry_returns_410_immediately(self, client):
        """
        REQ-ID: REQ-SHORT-004 | Scenario: SCN-004 | Type: error_case
        A URL created with expires_at in the past must immediately return 410 on redirect.
        """
        r = client.post(
            "/urls",
            json={
                "url": "https://www.example.com/expired",
                "expires_at": "2000-06-15T12:00:00Z",
            },
        )
        assert r.status_code == 201
        code = r.json()["short_code"]

        redirect = client.get(f"/{code}", follow_redirects=False)
        assert redirect.status_code == 410

    def test_future_expiry_allows_redirect(self, client):
        """
        REQ-ID: REQ-SHORT-004 | Scenario: SCN-004 context | Type: happy_path
        A URL with a future expires_at must redirect normally.
        """
        r = client.post(
            "/urls",
            json={
                "url": "https://www.example.com/future-expiry",
                "expires_at": "2099-01-01T00:00:00Z",
            },
        )
        assert r.status_code == 201
        code = r.json()["short_code"]

        redirect = client.get(f"/{code}", follow_redirects=False)
        assert redirect.status_code == 302

    def test_info_endpoint_shows_expires_at(self, client):
        """
        REQ-ID: REQ-SHORT-004, REQ-SHORT-003 | Scenario: SCN-004 | Type: happy_path
        GET /api/urls/{code} must return the expires_at field.
        """
        r = client.post(
            "/urls",
            json={
                "url": "https://www.example.com/expiry-info",
                "expires_at": "2099-12-31T00:00:00Z",
            },
        )
        code = r.json()["short_code"]

        info = client.get(f"/api/urls/{code}")
        assert info.status_code == 200
        assert info.json()["expires_at"] is not None
