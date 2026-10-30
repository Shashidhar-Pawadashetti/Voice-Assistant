"""Integration tests for health and readiness endpoints."""

import pytest
import httpx
from unittest.mock import patch


@pytest.mark.asyncio
async def test_health_live_endpoint(client: httpx.AsyncClient):
    """Verify /health/live returns HTTP 200 and ok status."""
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_health_ready_endpoint_healthy(client: httpx.AsyncClient):
    """Verify /health/ready returns status ok when dependencies are available."""
    with patch("app.api.v1.health.check_database_health", return_value=(True, None, 1.5)):
        with patch("app.core.llm.ollama.OllamaAdapter.check_health", return_value=(True, None, 2.0)):
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["dependencies"]["database"]["status"] == "UP"
            assert data["dependencies"]["ollama"]["status"] == "UP"


@pytest.mark.asyncio
async def test_health_ready_endpoint_db_down(client: httpx.AsyncClient):
    """Verify /health/ready returns 503 and degraded status when database is down."""
    with patch("app.api.v1.health.check_database_health", return_value=(False, "Connection refused", 50.0)):
        with patch("app.core.llm.ollama.OllamaAdapter.check_health", return_value=(True, None, 2.0)):
            response = await client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
            assert data["dependencies"]["database"]["status"] == "DOWN"


@pytest.mark.asyncio
async def test_api_v1_health_routes(client: httpx.AsyncClient):
    """Verify health endpoints mounted under /api/v1."""
    resp_live = await client.get("/api/v1/health/live")
    assert resp_live.status_code == 200
    assert resp_live.json()["status"] == "ok"
