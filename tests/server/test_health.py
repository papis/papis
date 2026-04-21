"""Tests for the health check endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from papis.server.app import app

client = TestClient(app)


def test_health() -> None:
    """GET /api/v1/health returns 200 with status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}
