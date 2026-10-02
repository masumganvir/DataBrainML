# DataWise AI — Enterprise System Architecture

## 1. Architectural Overview
DataWise AI is an enterprise-grade Autonomous Data Science and AutoML preparation platform engineered with a decoupled, asynchronous, and scalable infrastructure:

```
[ Client / Web UI ]
        │ (HTTP / WebSocket)
        ▼
[ Reverse Proxy / Nginx ]
        │
   ┌────┴────────────────────────┐
   │ FastAPI Application Cluster │
   │ (Distributed Rate Limiting) │
   └────┬──────────────────┬─────┘
        │                  │
   ┌────▼────────┐    ┌────▼────────┐    ┌──────────────┐
   │ PostgreSQL  │    │ Redis       │    │ S3 / MinIO   │
   │ (Truth DB)  │    │ (Locks/JobQ)│    │ Object Store │
   └─────────────┘    └────┬────────┘    └──────────────┘
                           │
                  ┌────────▼────────┐
                  │ Background      │
                  │ Worker Cluster  │
                  │ (LangGraph ML)  │
                  └─────────────────┘
```

## 2. Core Pillars
1. **API Layer (FastAPI)**: Non-blocking async endpoints handling authentication, telemetry, job dispatch, and model serving. CPU-heavy tasks are offloaded to workers.
2. **Relational Core (PostgreSQL)**: ACID compliant storage of 37 domain entities.
3. **High-Speed Cache & Coordinator (Redis)**: Atomic sliding-window rate limiting, distributed locking, deduplication/idempotency, and task priority queues.
4. **Binary Object Storage (S3 / MinIO)**: Encrypted, presigned storage for raw datasets, model weights (Joblib, ONNX), charts, and PDF reports.
5. **Execution Engine (LangGraph)**: 26 specialized agents organized into modular subgraphs coordinated by supervisors.
6. **Background Workers**: Redis-backed priority worker pool executing long-running ML training, SHAP analysis, and data profiling.

## 3. Configuration
System behavior is strictly governed by environment variables in `.env` (validated through Pydantic `Settings`).

## 4. Failure Scenarios & Resilience
- **Redis Crash**: Redis client automatically switches to graceful in-memory fallback to avoid total system blackout.
- **Compute Exhaustion**: Workers poll priority queues (`default`, `expensive`). Heavy Optuna runs are isolated from real-time API requests.
- **Node Failover**: Stateless FastAPI instances share state via Redis and PostgreSQL.
