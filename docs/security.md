# Security & Compliance

HealthChain includes built-in support for API key authentication, audit logging, and TLS — configured via `healthchain.yaml` and enforced at runtime by the gateway middleware stack.

---

## API key authentication

Enable inbound authentication by setting `security.auth: api-key` in `healthchain.yaml`:

```yaml
security:
  auth: api-key
```

Then set the expected key in `.env`:

```bash
HEALTHCHAIN_API_KEY=your-key-here
```

All routes except `/health`, `/docs`, `/redoc`, and `/openapi.json` will require the key on every request. Pass it as a Bearer token or an `X-API-Key` header:

```bash
# Bearer token
curl -H "Authorization: Bearer your-key-here" http://localhost:8000/fhir/Patient/123

# X-API-Key header
curl -H "X-API-Key: your-key-here" http://localhost:8000/fhir/Patient/123
```

Missing or incorrect keys receive a `401 Unauthorized` response:

```json
{ "detail": "Invalid or missing API key" }
```

!!! warning "Missing env var"
If `HEALTHCHAIN_API_KEY` is not set when the service starts, a warning is logged and all authenticated requests will be rejected. The service still starts — misconfiguration is visible without crashing.

---

## Audit logging

Set `compliance.audit_log` to a file path to enable per-request audit logging:

```yaml
compliance:
  audit_log: ./logs/audit.jsonl
```

The log directory is created automatically if it does not exist. Each request appends one JSON line:

```json
{
  "timestamp": "2026-05-06T10:23:41.123456+00:00",
  "method": "GET",
  "path": "/fhir/Patient/123",
  "status_code": 200,
  "duration_ms": 14.2,
  "request_id": "a1b2c3d4-...",
  "user": "api-key"
}
```

`request_id` uses the `X-Request-ID` header if present, otherwise a UUID is generated. `user` is populated when `api-key` auth is enabled, and `null` otherwise.

Log writes are non-blocking — IO errors are swallowed so a full disk or permission issue does not take down the service.

---

## TLS

Enable TLS by pointing `healthchain.yaml` at your certificate and key:

```yaml
security:
  tls:
    enabled: true
    cert_path: ./certs/server.crt
    key_path: ./certs/server.key
```

HealthChain passes these to uvicorn automatically when `healthchain serve` starts — no extra flags needed.

**Generating a self-signed certificate for local testing:**

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key \
  -out certs/server.crt -days 365 -nodes \
  -subj "/CN=localhost"
```

**For production**, use a certificate issued by a trusted CA. If you're deploying behind a reverse proxy (nginx, Caddy, an NHS load balancer), terminate TLS at the proxy and leave `tls.enabled: false` in HealthChain — the proxy handles the certificate, HealthChain handles the application.
