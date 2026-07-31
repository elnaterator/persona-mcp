"""Contract tests for POST /internal/backup — registration gate and token guard."""

from typing import Any

import pytest
from psycopg import Connection
from starlette.testclient import TestClient

_TOKEN = "backup-token-abc"


class FakeS3:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"ETag": "fake"}


def _make_client(db_conn: Connection[Any] | None) -> TestClient:
    from fastapi import FastAPI

    from pktx.api.routes import create_router
    from pktx.resume_service import ResumeService

    conn: Any = db_conn
    app = FastAPI()
    app.include_router(create_router(ResumeService(conn), db_conn=conn))
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> FakeS3:
    """Enable backups and stub out S3."""
    s3 = FakeS3()
    monkeypatch.setenv("PKTX_BACKUP_BUCKET", "pktx-backups-test")
    monkeypatch.setenv("PKTX_BACKUP_TOKEN", _TOKEN)
    monkeypatch.setenv("PKTX_ENV", "test")
    monkeypatch.setattr("pktx.backup_service.upload_backup", lambda *a, **k: None)
    return s3


class TestRegistrationGate:
    def test_route_absent_when_unconfigured(
        self, db_conn: Connection[Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PKTX_BACKUP_BUCKET", raising=False)
        monkeypatch.delenv("PKTX_BACKUP_TOKEN", raising=False)

        response = _make_client(db_conn).post("/internal/backup")

        assert response.status_code == 404

    def test_route_absent_without_a_db_connection(
        self, db_conn: Connection[Any], monkeypatch: pytest.MonkeyPatch, configured: Any
    ) -> None:
        from fastapi import FastAPI

        from pktx.api.routes import create_router
        from pktx.resume_service import ResumeService

        app = FastAPI()
        app.include_router(create_router(ResumeService(db_conn)))  # type: ignore[arg-type]

        assert TestClient(app).post("/internal/backup").status_code == 404

    def test_route_present_when_configured(
        self, db_conn: Connection[Any], configured: Any
    ) -> None:
        response = _make_client(db_conn).post(
            "/internal/backup", headers={"x-pktx-backup-token": _TOKEN}
        )

        assert response.status_code == 200


class TestTokenGuard:
    def test_missing_token_is_rejected(
        self, db_conn: Connection[Any], configured: Any
    ) -> None:
        assert _make_client(db_conn).post("/internal/backup").status_code == 401

    def test_wrong_token_is_rejected(
        self, db_conn: Connection[Any], configured: Any
    ) -> None:
        response = _make_client(db_conn).post(
            "/internal/backup", headers={"x-pktx-backup-token": "nope"}
        )

        assert response.status_code == 401

    def test_valid_token_returns_backup_summary(
        self, db_conn: Connection[Any], configured: Any
    ) -> None:
        db_conn.execute(
            "INSERT INTO users (id, email) VALUES ('backup_u', 'b@test.com') "
            "ON CONFLICT (id) DO NOTHING"
        )

        body = (
            _make_client(db_conn)
            .post("/internal/backup", headers={"x-pktx-backup-token": _TOKEN})
            .json()
        )

        assert body["key"].startswith("backups/")
        assert "pktx-test-" in body["key"]
        assert body["bytes"] > 0
        assert body["tables"]["users"] >= 1


class TestFailureHandling:
    def test_upload_failure_returns_500(
        self, db_conn: Connection[Any], configured: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def boom(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("s3 unavailable")

        monkeypatch.setattr("pktx.backup_service.upload_backup", boom)

        response = _make_client(db_conn).post(
            "/internal/backup", headers={"x-pktx-backup-token": _TOKEN}
        )

        assert response.status_code == 500
        assert "Backup failed" in response.json()["detail"]
