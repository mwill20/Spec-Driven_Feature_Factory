# Test suite — API contract and health endpoint (REQ-SHORT-006)
# Generated from: prompts/test-generator.yaml
# Covers: health endpoint, delete endpoint, error response schema, 404 handling

import pytest


class TestApiContract:
    """REQ-SHORT-006"""

    def test_health_endpoint_returns_200(self, client):
        """
        REQ-ID: REQ-SHORT-006 | Type: integration
        GET /api/health must return 200 with status, version, and timestamp fields.
        """
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_delete_existing_url_returns_204(self, client):
        """
        REQ-ID: REQ-SHORT-006 | Type: integration
        DELETE /api/urls/{code} on an existing code must return 204 No Content.
        """
        r = client.post("/urls", json={"url": "https://www.example.com/to-delete"})
        code = r.json()["short_code"]

        response = client.delete(f"/api/urls/{code}")
        assert response.status_code == 204

    def test_delete_nonexistent_url_returns_404(self, client):
        """
        REQ-ID: REQ-SHORT-006 | Scenario: SCN-009 context | Type: error_case
        DELETE /api/urls/{nonexistent_code} must return 404.
        """
        response = client.delete("/api/urls/zzz999")
        assert response.status_code == 404

    def test_deleted_url_no_longer_redirects(self, client):
        """
        REQ-ID: REQ-SHORT-006 | Type: integration | edge_case
        After deletion, GET /{code} must return 404.
        """
        r = client.post(
            "/urls", json={"url": "https://www.example.com/delete-then-redirect"}
        )
        code = r.json()["short_code"]

        client.delete(f"/api/urls/{code}")

        redirect = client.get(f"/{code}", follow_redirects=False)
        assert redirect.status_code == 404

    def test_get_info_for_nonexistent_code_returns_404(self, client):
        """
        REQ-ID: REQ-SHORT-006 | Scenario: SCN-009 | Type: error_case
        GET /api/urls/{nonexistent_code} must return 404.
        """
        response = client.get("/api/urls/zzz999")
        assert response.status_code == 404

    def test_openapi_docs_endpoint_is_available(self, client):
        """
        REQ-ID: REQ-SHORT-006 | Type: integration
        GET /docs must return 200 (FastAPI auto-generates OpenAPI UI).
        """
        response = client.get("/docs")
        assert response.status_code == 200
