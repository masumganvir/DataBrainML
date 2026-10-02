# Observability, Telemetry & Health Monitoring

## 1. Purpose
Provides end-to-end operational visibility across the distributed system: API response times, model inference percentiles, database query latencies, Redis queue depths, and container health probes.

## 2. Health Probes Specification
- `GET /health`: Basic service status.
- `GET /health/live`: Container liveness probe (200 OK).
- `GET /health/ready`: Deep dependency readiness check:
  - Database (`SELECT 1`)
  - Redis (`PING`)
  - Object Storage (`head_bucket` / local store check)
  Returns 503 Service Unavailable if any required component is degraded.
- `GET /api/v1/health/metrics`: In-process telemetry summary.

## 3. Metrics Tracked
- API request duration & HTTP status code distribution.
- Rate limiting 429 throttle rate.
- Model inference latency percentiles (`p50`, `p95`, `p99`).
- Worker job counts and completion rates.

## 4. Prometheus & Grafana Integration
- Enable monitoring profile in Docker Compose:
  ```bash
  docker compose --profile monitoring up -d
  ```
- Grafana dashboard accessible at `http://localhost:3001` (admin/admin).
- Prometheus scraping `/api/v1/health/metrics` at 15-second intervals.
