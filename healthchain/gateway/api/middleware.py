import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
    # Uptime/monitoring probes read the aggregate gateway status without a key
    "/gateway/status",
}

# FHIR AuditEvent action codes (ITI-20 / IHE ATNA)
_HTTP_AUDIT_ACTION = {
    "GET": "R",
    "HEAD": "R",
    "POST": "C",
    "PUT": "U",
    "PATCH": "U",
    "DELETE": "D",
}


def _audit_outcome(status_code: int) -> str:
    """Map an HTTP status to a FHIR AuditEvent outcome code."""
    if status_code >= 500:
        return "8"  # serious failure
    # Non-server errors mean the gateway handled the request successfully
    return "0"


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Enforce API-key authentication on all non-exempt routes.

    Only instantiated when security.auth is 'api-key' in healthchain.yaml.
    Reads the expected key from the HEALTHCHAIN_API_KEY environment variable.
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self._key = os.environ.get("HEALTHCHAIN_API_KEY")
        if not self._key:
            logger.warning(
                "security.auth is 'api-key' but HEALTHCHAIN_API_KEY is not set — "
                "all authenticated requests will be rejected"
            )

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        # Requests originating from internal HealthChain services are
        # authenticated upstream by the ingress/service mesh, which sets this
        # header. Skip the API-key check for those to avoid double auth.
        if request.headers.get("X-Internal-Request", "").lower() == "true":
            request.state.authenticated_user = "internal-service"
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided = auth_header[len("Bearer ") :]
        else:
            provided = request.headers.get("X-API-Key", "")

        if not provided or provided != self._key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        request.state.authenticated_user = "api-key"
        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Append one JSONL entry per request to the configured audit log path.

    Only instantiated when compliance.audit_log is set in healthchain.yaml.
    Log writes are non-blocking — IO errors are swallowed to avoid impacting
    request handling.
    """

    def __init__(self, app, audit_log_path: str) -> None:
        super().__init__(app)
        self._path = Path(audit_log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        response = await call_next(request)

        # Echo request id so clients can correlate gateway logs with responses
        response.headers["X-Request-ID"] = request_id

        if response.status_code == 401:
            return response

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        entry = {
            # Local wall-clock time is friendlier for operators reading the log
            # on the host than UTC offsets.
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
            "user": _get_user(request),
            "action": _HTTP_AUDIT_ACTION.get(request.method.upper(), "E"),
            "outcome": _audit_outcome(response.status_code),
        }

        try:
            with open(self._path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        return response


def _get_user(request: Request) -> Optional[str]:
    """Extract authenticated user identity from request state set by APIKeyMiddleware."""
    return getattr(request.state, "authenticated_user", None)
