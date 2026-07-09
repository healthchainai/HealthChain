"""Tests for gateway request metrics collection and /metrics endpoint."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from healthchain.gateway.api.metrics import (
    MetricsCollector,
    RequestMetricsMiddleware,
    get_metrics_collector,
    metrics_json_response,
    normalize_path,
)


def test_normalize_path_collapses_ids():
    assert normalize_path("/fhir/Patient/abc-123-def") == "/fhir/Patient/abc-123-def"
    assert (
        normalize_path("/fhir/Patient/a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        == "/fhir/Patient/{id}"
    )
    assert normalize_path("/items/42/details") == "/items/{id}/details"


def test_metrics_collector_records_and_snapshots():
    collector = MetricsCollector()
    collector.record("GET", "/fhir/Patient/1", 200, 12.5)
    collector.record("GET", "/fhir/Patient/2", 404, 3.0)
    collector.record("POST", "/fhir/Observation", 201, 45.0)

    snap = collector.snapshot()
    assert snap["total_requests"] == 3
    assert snap["total_errors"] == 1
    assert "GET /fhir/Patient/{id}" in snap["routes"]
    assert snap["routes"]["GET /fhir/Patient/{id}"]["request_count"] == 2
    assert snap["routes"]["GET /fhir/Patient/{id}"]["error_count"] == 1


def test_metrics_collector_reset_clears_state():
    collector = MetricsCollector()
    collector.record("GET", "/health", 200, 1.0)
    collector.reset()
    assert collector.snapshot()["total_requests"] == 0


def test_request_metrics_middleware_records_requests():
    collector = MetricsCollector()
    app = FastAPI()

    @app.get("/api/data")
    def data():
        return {"ok": True}

    @app.get("/api/error")
    def error():
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=500, content={"bad": True})

    app.add_middleware(RequestMetricsMiddleware, collector=collector)
    client = TestClient(app, raise_server_exceptions=False)

    client.get("/api/data")
    client.get("/api/error")

    snap = collector.snapshot()
    assert snap["total_requests"] == 2
    assert snap["routes"]["GET /api/data"]["request_count"] == 1


def test_request_metrics_middleware_skips_exempt_paths():
    collector = MetricsCollector()
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.add_middleware(RequestMetricsMiddleware, collector=collector)
    client = TestClient(app)
    client.get("/health")

    assert collector.snapshot()["total_requests"] == 0


def test_metrics_json_response():
    collector = MetricsCollector()
    collector.record("GET", "/test", 200, 5.0)
    response = metrics_json_response(collector)
    assert response.status_code == 200
    assert "total_requests" in response.body.decode()


def test_get_metrics_collector_returns_singleton():
    a = get_metrics_collector()
    b = get_metrics_collector()
    assert a is b


def test_snapshot_includes_error_rate():
    collector = MetricsCollector()
    collector.record("GET", "/a", 200, 5.0)
    collector.record("GET", "/b", 500, 5.0)
    snap = collector.snapshot()
    assert snap["error_rate"] == 0.5


def test_slow_requests_captured_above_threshold():
    collector = MetricsCollector(slow_threshold_ms=100.0, slow_sample_size=5)
    collector.record_slow("GET", "/fhir/Patient?name=x", 200, 250.0)
    collector.record_slow("GET", "/fhir/Observation", 200, 10.0)  # below threshold
    snap = collector.snapshot()
    assert len(snap["slow_requests"]) == 1
    assert snap["slow_requests"][0]["duration_ms"] == 250.0


def test_slow_requests_ring_buffer_bounded():
    collector = MetricsCollector(slow_threshold_ms=0.0, slow_sample_size=3)
    for i in range(10):
        collector.record_slow("GET", f"/x/{i}", 200, 5.0)
    assert len(collector.snapshot()["slow_requests"]) == 3
