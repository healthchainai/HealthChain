"""In-process request metrics for the HealthChain gateway.

Collects per-route latency and error counters and exposes them via a JSON
``/metrics`` endpoint.  Designed as a lightweight alternative to pulling in
Prometheus/OpenTelemetry for single-process deployments.
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Collapse numeric IDs and UUIDs so /fhir/Patient/abc-123 → /fhir/Patient/{id}
_PATH_ID_RE = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    r"|/\d+"
)


def normalize_path(path: str) -> str:
    """Reduce cardinality by replacing dynamic path segments with placeholders."""
    return _PATH_ID_RE.sub("/{id}", path)


@dataclass
class RouteStats:
    """Rolling statistics for a single (method, normalized_path) pair."""

    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: Optional[float] = None
    max_duration_ms: Optional[float] = None
    status_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record(self, status_code: int, duration_ms: float) -> None:
        self.request_count += 1
        self.total_duration_ms += duration_ms
        if self.min_duration_ms is None or duration_ms < self.min_duration_ms:
            self.min_duration_ms = duration_ms
        if self.max_duration_ms is None or duration_ms > self.max_duration_ms:
            self.max_duration_ms = duration_ms

        bucket = f"{status_code // 100}xx"
        self.status_counts[bucket] += 1
        if status_code >= 400:
            self.error_count += 1

    @property
    def avg_duration_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return round(self.total_duration_ms / self.request_count, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_duration_ms": self.avg_duration_ms,
            "min_duration_ms": self.min_duration_ms,
            "max_duration_ms": self.max_duration_ms,
            "status_counts": dict(self.status_counts),
        }


class MetricsCollector:
    """Thread-safe in-memory metrics store shared by middleware and /metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._routes: Dict[Tuple[str, str], RouteStats] = {}
        self._started_at = time.time()

    def record(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        key = (method.upper(), normalize_path(path))
        with self._lock:
            if key not in self._routes:
                self._routes[key] = RouteStats()
            self._routes[key].record(status_code, duration_ms)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            routes = {
                f"{method} {path}": stats.to_dict()
                for (method, path), stats in sorted(self._routes.items())
            }
            total_requests = sum(s.request_count for s in self._routes.values())
            total_errors = sum(s.error_count for s in self._routes.values())

        return {
            "uptime_seconds": round(time.time() - self._started_at, 1),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "routes": routes,
        }

    def reset(self) -> None:
        with self._lock:
            self._routes.clear()
            self._started_at = time.time()


# Module-level singleton used when middleware is enabled
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Record request latency and status-code distribution per route."""

    _EXEMPT = {"/metrics", "/health", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app, collector: Optional[MetricsCollector] = None) -> None:
        super().__init__(app)
        self._collector = collector or get_metrics_collector()

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._EXEMPT:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        self._collector.record(
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def metrics_json_response(collector: Optional[MetricsCollector] = None) -> JSONResponse:
    """Build a JSONResponse from the current metrics snapshot."""
    data = (collector or get_metrics_collector()).snapshot()
    return JSONResponse(content=data)
