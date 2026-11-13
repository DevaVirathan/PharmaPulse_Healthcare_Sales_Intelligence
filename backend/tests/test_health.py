from fastapi.testclient import TestClient


def test_health_returns_expected_payload(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "application": "PharmaPulse"}


def test_root_points_to_api_and_docs(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["api"] == "/api/v1"
    assert body["docs"] == "/docs"
