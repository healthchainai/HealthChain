"""Tests for FHIR client retry, patch, vread, and history interactions."""

import json

import httpx
import pytest
from unittest.mock import Mock, patch

from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.patient import Patient

from healthchain.gateway.clients.fhir.base import FHIRAuthConfig
from healthchain.gateway.clients.fhir.sync import FHIRClient


@pytest.fixture
def mock_auth_config():
    return FHIRAuthConfig(
        base_url="https://test.fhir.org/R4",
        client_id="test_client",
        client_secret="test_secret",
        token_url="https://test.fhir.org/oauth/token",
        retry_max_attempts=3,
        retry_backoff_base=0.01,
    )


@pytest.fixture
def fhir_client(mock_auth_config):
    with patch("healthchain.gateway.clients.auth.OAuth2TokenManager") as mgr_cls:
        mgr = Mock()
        mgr.get_access_token = Mock(return_value="test_token")
        mgr_cls.return_value = mgr
        client = FHIRClient(auth_config=mock_auth_config)
        client.token_manager = mgr
        return client


@pytest.fixture
def mock_response():
    response = Mock(spec=httpx.Response)
    response.is_success = True
    response.status_code = 200
    response.json.return_value = {"resourceType": "Patient", "id": "123"}
    return response


def test_fhir_http_get_retries_transient_failure(fhir_client, mock_response, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)
    calls = {"n": 0}

    def flaky_get(*_a, **_kw):
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectError("reset")
        return mock_response

    with patch.object(fhir_client.client, "get", side_effect=flaky_get):
        with patch.object(
            fhir_client, "_get_headers", return_value={"Authorization": "Bearer t"}
        ):
            patient = fhir_client.read(Patient, "123")

    assert patient.id == "123"
    assert calls["n"] == 2


def test_fhir_patch_sends_json_patch_content(fhir_client, mock_response):
    patch_body = [{"op": "replace", "path": "/active", "value": False}]
    mock_response.json.return_value = {
        "resourceType": "Patient",
        "id": "123",
        "active": False,
    }

    with patch.object(
        fhir_client.client, "patch", return_value=mock_response
    ) as mock_patch:
        with patch.object(
            fhir_client, "_get_headers", return_value={"Authorization": "Bearer t"}
        ):
            result = fhir_client.patch(Patient, "123", patch_body)

    assert result.active is False
    _, kwargs = mock_patch.call_args
    assert kwargs["headers"]["Content-Type"] == "application/json-patch+json"
    assert json.loads(kwargs["content"]) == patch_body


def test_fhir_vread_hits_history_version_url(fhir_client, mock_response):
    with patch.object(
        fhir_client.client, "get", return_value=mock_response
    ) as mock_get:
        with patch.object(
            fhir_client, "_get_headers", return_value={"Authorization": "Bearer t"}
        ):
            fhir_client.vread(Patient, "123", "v2")

    called_url = mock_get.call_args[0][0]
    assert called_url.endswith("Patient/123/_history/v2")


def test_fhir_history_returns_bundle(fhir_client):
    bundle_response = Mock(spec=httpx.Response)
    bundle_response.is_success = True
    bundle_response.status_code = 200
    bundle_response.json.return_value = {
        "resourceType": "Bundle",
        "type": "history",
        "entry": [],
    }

    with patch.object(
        fhir_client.client, "get", return_value=bundle_response
    ) as mock_get:
        with patch.object(
            fhir_client, "_get_headers", return_value={"Authorization": "Bearer t"}
        ):
            bundle = fhir_client.history(Patient, "123")

    assert isinstance(bundle, Bundle)
    called_url = mock_get.call_args[0][0]
    assert called_url.endswith("Patient/123/_history")
