# Test suite — Analytics tracking (REQ-SHORT-003)
# Generated from: prompts/test-generator.yaml
# Covers: SCN-003 (click count increments, last_accessed update)

import pytest

from tests.conftest import VALID_URL


class TestAnalytics:
    """REQ-SHORT-003"""

    def _create_url(self, client, url: str) -> str:
        r = client.post("/urls", json={"url": url})
        assert r.status_code in (200, 201)
        return r.json()["short_code"]

    def _get_info(self, client, code: str) -> dict:
        r = client.get(f"/api/urls/{code}")
        assert r.status_code == 200
        return r.json()

    def test_initial_click_count_is_zero(self, client):
        """
        REQ-ID: REQ-SHORT-003 | Scenario: SCN-003 context | Type: happy_path
        A freshly created URL must have click_count of 0.
        """
        code = self._create_url(client, "https://www.example.com/fresh")
        info = self._get_info(client, code)

        assert info["click_count"] == 0

    def test_click_count_increments_on_each_redirect(self, client):
        """
        REQ-ID: REQ-SHORT-003 | Scenario: SCN-003 | Type: happy_path
        Each successful redirect must increment click_count by exactly 1.
        """
        code = self._create_url(client, "https://www.example.com/analytics-test")

        for i in range(3):
            r = client.get(f"/{code}", follow_redirects=False)
            assert r.status_code == 302

        info = self._get_info(client, code)
        assert info["click_count"] == 3

    def test_last_accessed_updates_after_redirect(self, client):
        """
        REQ-ID: REQ-SHORT-003 | Scenario: SCN-003 | Type: happy_path
        last_accessed must be non-null after at least one redirect.
        """
        code = self._create_url(client, "https://www.example.com/last-accessed")

        assert self._get_info(client, code)["last_accessed"] is None

        client.get(f"/{code}", follow_redirects=False)

        info = self._get_info(client, code)
        assert info["last_accessed"] is not None

    def test_referrer_stored_from_referer_header(self, client):
        """
        REQ-ID: REQ-SHORT-003 | Scenario: SCN-003 | Type: happy_path
        The HTTP Referer header value must be stored in the referrer field.
        """
        code = self._create_url(client, "https://www.example.com/referrer-test")

        client.get(
            f"/{code}",
            follow_redirects=False,
            headers={"Referer": "https://www.google.com/"},
        )

        info = self._get_info(client, code)
        assert info["referrer"] == "https://www.google.com/"

    def test_analytics_not_incremented_for_expired_url(self, client):
        """
        REQ-ID: REQ-SHORT-003, REQ-SHORT-004 | Scenario: SCN-004 | Type: edge_case
        An expired URL request must not increment click_count.
        """
        code = self._create_url(
            client,
            "https://www.example.com/no-analytics-if-expired",
        )
        # Patch expiry by re-creating with past date (new URL different code)
        past_code_resp = client.post(
            "/urls",
            json={
                "url": "https://www.example.com/expired-analytics",
                "expires_at": "2020-01-01T00:00:00Z",
            },
        )
        past_code = past_code_resp.json()["short_code"]

        client.get(f"/{past_code}", follow_redirects=False)  # should return 410

        info = self._get_info(client, past_code)
        assert info["click_count"] == 0, (
            "click_count must not increment on an expired URL redirect attempt"
        )

    def test_get_url_info_returns_all_analytics_fields(self, client):
        """
        REQ-ID: REQ-SHORT-003, REQ-SHORT-006 | Scenario: SCN-003 | Type: happy_path
        GET /api/urls/{code} must include click_count, last_accessed, referrer.
        """
        code = self._create_url(client, "https://www.example.com/info-fields")
        info = self._get_info(client, code)

        assert "click_count" in info
        assert "last_accessed" in info
        assert "referrer" in info
        assert "created_at" in info
        assert "is_active" in info
