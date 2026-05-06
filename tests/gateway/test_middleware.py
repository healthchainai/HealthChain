"""Tests for AuditLogMiddleware and APIKeyMiddleware."""

import json
import pytest
from unittest.mock import patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from healthchain.gateway.api.middleware import APIKeyMiddleware, AuditLogMiddleware


# ── helpers ──────────────────────────────────────────────────────────────────


def _api_key_app():
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/docs")
    def docs():
        return {}

    @app.get("/redoc")
    def redoc():
        return {}

    @app.get("/openapi.json")
    def openapi():
        return {}

    @app.get("/data")
    def data():
        return {"result": "ok"}

    app.add_middleware(APIKeyMiddleware)
    return app


def _audit_app(log_path: str):
    app = FastAPI()

    @app.get("/data")
    def data():
        return {"result": "ok"}

    app.add_middleware(AuditLogMiddleware, audit_log_path=log_path)
    return app


# ── APIKeyMiddleware ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("path", ["/health", "/docs", "/redoc", "/openapi.json"])
def test_api_key_exempt_paths_pass_through(monkeypatch, path):
    monkeypatch.setenv("HEALTHCHAIN_API_KEY", "secret")
    client = TestClient(_api_key_app(), raise_server_exceptions=False)
    assert client.get(path).status_code == 200


def test_api_key_bearer_token_accepted(monkeypatch):
    monkeypatch.setenv("HEALTHCHAIN_API_KEY", "my-secret")
    client = TestClient(_api_key_app(), raise_server_exceptions=False)
    response = client.get("/data", headers={"Authorization": "Bearer my-secret"})
    assert response.status_code == 200


def test_api_key_x_api_key_header_accepted(monkeypatch):
    monkeypatch.setenv("HEALTHCHAIN_API_KEY", "my-secret")
    client = TestClient(_api_key_app(), raise_server_exceptions=False)
    response = client.get("/data", headers={"X-API-Key": "my-secret"})
    assert response.status_code == 200


def test_api_key_wrong_key_rejected(monkeypatch):
    monkeypatch.setenv("HEALTHCHAIN_API_KEY", "my-secret")
    client = TestClient(_api_key_app(), raise_server_exceptions=False)
    response = client.get("/data", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_api_key_missing_header_rejected(monkeypatch):
    monkeypatch.setenv("HEALTHCHAIN_API_KEY", "my-secret")
    client = TestClient(_api_key_app(), raise_server_exceptions=False)
    assert client.get("/data").status_code == 401
    assert client.get("/data").json() == {"detail": "Invalid or missing API key"}


def test_api_key_missing_env_var_logs_warning_and_rejects(monkeypatch):
    monkeypatch.delenv("HEALTHCHAIN_API_KEY", raising=False)
    with patch("healthchain.gateway.api.middleware.logger") as mock_logger:
        client = TestClient(_api_key_app(), raise_server_exceptions=False)
        client.get("/data")  # triggers middleware stack build
        mock_logger.warning.assert_called_once()
    assert client.get("/data").status_code == 401


def test_api_key_sets_authenticated_user_on_state(monkeypatch):
    monkeypatch.setenv("HEALTHCHAIN_API_KEY", "secret")
    captured_state = {}

    app = FastAPI()

    @app.get("/data")
    async def data(request: Request):
        captured_state["user"] = getattr(request.state, "authenticated_user", None)
        return {}

    app.add_middleware(APIKeyMiddleware)
    client = TestClient(app, raise_server_exceptions=False)
    client.get("/data", headers={"Authorization": "Bearer secret"})
    assert captured_state["user"] == "api-key"


# ── AuditLogMiddleware ────────────────────────────────────────────────────────


def test_audit_log_creates_file_and_directory(tmp_path):
    log_path = tmp_path / "nested" / "dir" / "audit.jsonl"
    client = TestClient(_audit_app(str(log_path)), raise_server_exceptions=False)
    client.get("/data")
    assert log_path.exists()


def test_audit_log_writes_one_entry_per_request(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    client = TestClient(_audit_app(str(log_path)), raise_server_exceptions=False)
    client.get("/data")
    client.get("/data")
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 2


def test_audit_log_entry_fields(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    client = TestClient(_audit_app(str(log_path)), raise_server_exceptions=False)
    client.get("/data")
    entry = json.loads(log_path.read_text().strip())
    assert entry["method"] == "GET"
    assert entry["path"] == "/data"
    assert entry["status_code"] == 200
    assert "timestamp" in entry
    assert "duration_ms" in entry
    assert "request_id" in entry


def test_audit_log_uses_x_request_id_header(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    client = TestClient(_audit_app(str(log_path)), raise_server_exceptions=False)
    client.get("/data", headers={"X-Request-ID": "test-id-123"})
    entry = json.loads(log_path.read_text().strip())
    assert entry["request_id"] == "test-id-123"


def test_audit_log_generates_uuid_when_no_request_id(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    client = TestClient(_audit_app(str(log_path)), raise_server_exceptions=False)
    client.get("/data")
    entry = json.loads(log_path.read_text().strip())
    assert len(entry["request_id"]) == 36  # UUID4 format


def test_audit_log_swallows_io_errors(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    client = TestClient(_audit_app(str(log_path)), raise_server_exceptions=False)
    with patch("builtins.open", side_effect=OSError("disk full")):
        response = client.get("/data")
    assert response.status_code == 200


def test_audit_log_user_is_none_without_auth(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    client = TestClient(_audit_app(str(log_path)), raise_server_exceptions=False)
    client.get("/data")
    entry = json.loads(log_path.read_text().strip())
    assert entry["user"] is None


def test_audit_log_user_populated_when_auth_state_set(tmp_path):
    log_path = tmp_path / "audit.jsonl"

    app = FastAPI()

    @app.get("/data")
    async def data(request: Request):
        request.state.authenticated_user = "api-key"
        return {}

    app.add_middleware(AuditLogMiddleware, audit_log_path=str(log_path))
    client = TestClient(app, raise_server_exceptions=False)
    client.get("/data")
    entry = json.loads(log_path.read_text().strip())
    assert entry["user"] == "api-key"
