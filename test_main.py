from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_info_default(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)

    response = client.get("/info")

    assert response.status_code == 200
    assert response.json() == {"environment": "local"}


def test_info_configured(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test-environment")

    response = client.get("/info")

    assert response.status_code == 200
    assert response.json() == {"environment": "test-environment"}