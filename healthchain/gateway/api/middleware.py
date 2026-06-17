import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


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

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
            "user": _get_user(request),
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
