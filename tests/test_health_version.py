import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == settings.APP_VERSION
    assert data["service"] == "secure-code-review-bot"

def test_version_check():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == settings.APP_VERSION
    assert data["name"] == settings.APP_NAME
