# API Reference & Enterprise Contract

## 1. Authentication
Protected endpoints require either a JWT Bearer token or an API key:
- Header: `Authorization: Bearer <jwt_access_token>`
- Header: `X-API-Key: dw_live_<api_key>`

## 2. Global Headers
- `X-Request-ID`: Distributed correlation ID (auto-generated if omitted).
- `X-Process-Time`: Wall-clock endpoint execution latency.
- `Retry-After`: Seconds to wait when receiving HTTP 429.
- `Idempotency-Key`: Prevents accidental duplicate execution on POST routes.

## 3. Core Endpoints Overview
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Container liveness |
| GET | `/health/ready` | Deep database/Redis readiness probe |
| POST | `/api/datasets` | Upload and sanitize untrusted dataset |
| GET | `/api/datasets/{id}` | Retrieve dataset metadata & column profile |
| POST | `/api/experiments` | Create ML experiment run |
| POST | `/api/models/train` | Enqueue background model training job |
| GET | `/api/models/registry` | List registered and promoted models |
| POST | `/api/models/promote` | Promote model candidate to Staging/Production |
| POST | `/api/inference/predict`| Real-time low-latency model inference |
| GET | `/api/jobs/{id}/status`| Real-time background worker status |
| GET | `/api/reports/download` | Download compiled PDF/HTML reports |
| POST | `/api/decisions` | Submit human-in-the-loop approvals |

## 4. Standard Rate Limit Error (HTTP 429)
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please slow down.",
  "retry_after": 30,
  "request_id": "c1f7b028-1111-4f40-8b1a-b6058495df22"
}
```
