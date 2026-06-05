from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import app


router = APIRouter()


@router.get("/api/test-unhandled-error")
def raise_unhandled_error():
    raise RuntimeError("database unavailable")


app.include_router(router)


def test_unhandled_exception_returns_json_response():
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/test-unhandled-error")

    assert response.status_code == 500
    assert response.json() == {
        "code": 500,
        "message": "internal server error",
        "data": {"detail": "database unavailable"},
    }
