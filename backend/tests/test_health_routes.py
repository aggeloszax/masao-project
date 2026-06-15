from fastapi.testclient import TestClient

from api.main import app


def test_health_is_liveness_without_dependency_checks() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_returns_200_when_dependencies_are_available(monkeypatch) -> None:
    async def db_ready() -> None:
        return None

    async def limiter_ready() -> None:
        return None

    monkeypatch.setattr("api.main.check_database_ready", db_ready)
    monkeypatch.setattr("api.main.check_rate_limiter_ready", limiter_ready)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "Masao Restaurant Chatbot API",
        "checks": {"database": "ok", "rate_limiter": "ok"},
    }


def test_ready_returns_503_when_database_is_unavailable(monkeypatch) -> None:
    async def db_not_ready() -> None:
        raise RuntimeError("database unavailable")

    async def limiter_ready() -> None:
        return None

    monkeypatch.setattr("api.main.check_database_ready", db_not_ready)
    monkeypatch.setattr("api.main.check_rate_limiter_ready", limiter_ready)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["database"] == "unavailable"
    assert response.json()["checks"]["rate_limiter"] == "ok"
