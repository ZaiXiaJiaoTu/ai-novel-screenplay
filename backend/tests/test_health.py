from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app


def test_health_check():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_database_health_check_success(monkeypatch):
    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, _statement):
            return None

    monkeypatch.setattr("app.routers.health_router.SessionLocal", lambda: FakeSession())
    client = TestClient(app)

    response = client.get("/api/health/db")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_database_health_check_failure(monkeypatch):
    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, Exception("bad password"))

    monkeypatch.setattr("app.routers.health_router.SessionLocal", lambda: FakeSession())
    client = TestClient(app)

    response = client.get("/api/health/db")

    assert response.status_code == 503
    assert response.json()["code"] == 503
    assert response.json()["data"]["status"] == "error"
