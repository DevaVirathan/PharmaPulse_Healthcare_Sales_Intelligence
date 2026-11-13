from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.main import app


class BrokenSession:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("database unavailable"))


def test_readiness_ok(client: TestClient, sqlite_session: Session) -> None:
    app.dependency_overrides[get_db] = lambda: sqlite_session
    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "available"}


def test_readiness_returns_503_without_leaking_details(client: TestClient) -> None:
    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "database": "unavailable"}
    assert "password" not in response.text.lower()
    assert "traceback" not in response.text.lower()
