import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


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
            # Placeholder: populated once API-key auth is wired in
            "user": _get_user(request),
        }

        try:
            with open(self._path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        return response


def _get_user(request: Request) -> Optional[str]:
    """Extract authenticated user identity from the request.

    Returns None until inbound auth middleware is wired in.
    """
    return None
