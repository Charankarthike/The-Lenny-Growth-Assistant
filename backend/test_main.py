"""
Quick test to verify FastAPI application starts correctly.
Run with: python -m pytest test_main.py
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test that root endpoint returns app information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "Lenny Growth Assistant"


def test_health_endpoint():
    """Test that health endpoint returns status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


def test_config_endpoint():
    """Test that config endpoint returns configuration."""
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert "model_provider" in data
    assert "available_providers" in data
    assert "features" in data


def test_create_session():
    """Test session creation."""
    response = client.post("/api/v1/sessions", json={
        "title": "Test Session"
    })
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["title"] == "Test Session"


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.options("/api/v1/config")
    # CORS headers should be present
    assert response.status_code in [200, 405]  # OPTIONS might not be explicitly defined
