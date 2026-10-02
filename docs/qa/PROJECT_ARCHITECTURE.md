# DataWise AI — Enterprise Architecture & System Specification

## 1. Executive Architecture Summary
DataWise AI is an enterprise-grade Autonomous Data Science, AutoML, Deep Learning, MLOps, and Decision Support Platform. The platform enables multi-tenant dataset ingestion, deep statistical profiling, exploratory data analysis (EDA), automated feature engineering, resilient baseline & model search, hyperparameter optimization, model explainability (SHAP), automated Jupyter notebook generation, PDF executive reporting, one-click artifact deployment, real-time inference serving, and continuous drift-driven retraining.

---

## 2. System Component Breakdown

### Component 1: Frontend Web Application
- **Purpose**: Interactive single-page application (SPA) providing visualization dashboards, project workspaces, AutoML lab controls, model registry, monitoring alerts, and real-time streaming agent chat.
- **Technology**: React 18.3, TypeScript 5.6, Vite 6.0, React Router DOM 6.28, Plotly.js, Lucide Icons, PrismJS syntax highlighter.
- **Dependencies**: Node.js v24+, Axios HTTP client, WebSocket API.
- **Entry Point**: `frontend/src/main.tsx` -> `frontend/src/App.tsx`.
- **API**: Connects to Backend REST at `/api/v1` and WebSocket streams at `/api/v1/stream/*`.
- **Database Dependency**: Indirect via REST API.
- **Security Boundary**: Runs in user browser sandbox. Strict Content Security Policy (CSP), token storage in memory/secure storage, input sanitization on all markdown and code previews.
- **Test Strategy**: Component unit tests, TypeScript type checks, ESLint AST validation, Playwright browser E2E workflows, responsive viewport verification.

### Component 2: Desktop Shell Application (Tauri)
- **Purpose**: Native cross-platform desktop wrapper for enterprise air-gapped or local workstation deployment.
- **Technology**: Tauri 1.5, Rust Edition 2021, WebKit / WebView2.
- **Dependencies**: Rust compiler, Cargo toolchain, Tauri CLI.
- **Entry Point**: `frontend/src-tauri/src/main.rs`, configured via `frontend/src-tauri/tauri.conf.json`.
- **API**: Communicates with local or remote backend through Tauri custom protocol and isolated HTTP client.
- **Database Dependency**: None directly; connects through backend API.
- **Security Boundary**: Native Tauri permission scopes (filesystem restricted to designated project directories, shell execution isolated, IPC command whitelisting).
- **Test Strategy**: Cargo build validation, Tauri configuration schema verification, native permission scope audit, launch/shutdown smoke test.

### Component 3: Backend API Gateway & Server
- **Purpose**: Asynchronous REST and WebSocket gateway exposing all core platform capabilities, request validation, authentication, rate limiting, and telemetry.
- **Technology**: Python 3.11–3.14, FastAPI 0.141, Starlette, Uvicorn, Pydantic v2, Python-Multipart.
- **Dependencies**: `backend/requirements.txt`, PostgreSQL asyncpg driver, Redis client, MinIO SDK.
- **Entry Point**: `backend/main.py` (`create_app()`).
- **API**: 
  - `/health`, `/health/live`, `/health/ready` (Kubernetes probes)
  - `/api/v1/sessions/*` (Project sessions, data ingestion, profiling, decisions)
  - `/api/v1/models/*` (Model registry, lineage, deployment)
  - `/api/v1/inference/*` (Real-time and batch model prediction)
  - `/api/v1/realtime/*` (AutoML execution and stream events)
- **Database Dependency**: Direct async connection pool (SQLAlchemy AsyncEngine + asyncpg/aiosqlite).
- **Security Boundary**: Distributed rate-limiting middleware, CORS origin validation, JWT token verification, RBAC permissions, output confidentiality sanitization gate.
- **Test Strategy**: Pytest suite, AsyncClient API contract tests, mock failure injection, HTTP parameter tampering tests.

### Component 4: Relational Truth Database
- **Purpose**: Relational schema maintaining 37 domain entities including Users, Organizations, Projects, Datasets, Columns, Experiments, Trials, Models, Deployments, Drift Metrics, and Audit Trails.
- **Technology**: PostgreSQL 16 (production) with SQLite/aiosqlite compatibility layer for isolated zero-dependency testing.
- **Dependencies**: SQLAlchemy 2.0 ORM, Alembic 1.20 migration manager.
- **Entry Point**: `backend/app/db/session.py`, `backend/app/db/models/entities.py`.
- **API**: Internal repository pattern and SQLAlchemy AsyncSession queries.
- **Database Dependency**: Self (Primary relational store).
- **Security Boundary**: Foreign key constraints, unique indexes, tenant isolation (OrgID/UserID scoping), parameterization preventing SQL injection, soft deletion.
- **Test Strategy**: Alembic migration downgrade/upgrade cycles, multi-tenant IDOR isolation tests, SQL injection fuzzer tests, rollback on transaction failure tests.

### Component 5: High-Speed Cache, Distributed Lock & Message Broker
- **Purpose**: Atomic sliding-window rate limiting, distributed mutex locks for concurrent training prevention, job queue dispatching, and transient caching.
- **Technology**: Redis 7 Alpine.
- **Dependencies**: `redis-py` (asyncio enabled).
- **Entry Point**: `backend/app/cache/redis_client.py`.
- **API**: Internal key-value, sorted set, and Pub/Sub interfaces.
- **Database Dependency**: None.
- **Security Boundary**: Internal network only; isolated Redis database indices; auto-failover to safe in-memory fallback cache if Redis drops.
- **Test Strategy**: Concurrency lock verification, rate limit window exhaustion tests, Redis failover & automatic recovery injection.

### Component 6: Binary Object Storage
- **Purpose**: Secure encrypted persistence of raw CSV/Parquet uploads, trained model artifacts (`.joblib`, `.pt`, `.onnx`), generated charts, and exportable PDF reports.
- **Technology**: MinIO (S3-compatible API) with local filesystem fallback (`backend/artifacts`, `backend/data/uploads`).
- **Dependencies**: `minio` Python SDK, `aiofiles`.
- **Entry Point**: `backend/app/storage/` and `backend/app/tools/storage.py`.
- **API**: S3 presigned URLs, streaming object download/upload.
- **Database Dependency**: References stored in `Dataset` and `ModelArtifact` database records.
- **Security Boundary**: Presigned expiring URLs, path-traversal sanitization (`secure_filename`), MIME-type verification, magic number validation.
- **Test Strategy**: Malformed file upload tests, path traversal filename injection (`../../etc/passwd`), storage quota exhaustion tests.

### Component 7: Agent Orchestration Engine (LangGraph Multi-Agent System)
- **Purpose**: Coordinated multi-agent workflow managing complex end-to-end data science pipelines across 26 specialized agents organized into subgraphs.
- **Technology**: LangGraph 1.2+, LangChain Core, Pydantic state graphs.
- **Dependencies**: `langgraph`, `langchain-core`, LLM providers (Google Gemini / OpenAI / Ollama).
- **Entry Point**: `backend/graphs/master_graph.py`, `backend/agents/00_orchestrator_agent/`.
- **Subgraphs**:
  - Ingestion & Profiling Subgraph (`backend/graphs/ingestion_graph.py`)
  - Data Analysis & EDA Subgraph (`backend/graphs/data_analysis_graph.py`)
  - Preprocessing & Cleaning Subgraph (`backend/graphs/preprocessing_graph.py`)
  - Feature Engineering Subgraph (`backend/graphs/feature_engineering_graph.py`)
  - Model Selection & Training Subgraph (`backend/graphs/training_graph.py`)
  - Optimization & Hyperparameter Subgraph (`backend/graphs/optimization_graph.py`)
  - Evaluation & Explainability Subgraph (`backend/graphs/evaluation_graph.py`)
  - Deployment & Registry Subgraph (`backend/graphs/deployment_graph.py`)
  - Monitoring & Drift Subgraph (`backend/graphs/monitoring_graph.py`)
  - Online Learning & Retraining Subgraph (`backend/graphs/online_learning_graph.py`)
  - Autonomous Recovery Subgraph (`backend/graphs/recovery_graph.py`)
- **API**: Invocable via graph execution runners and streaming event generators.
- **Database Dependency**: Agent state checkpointing and telemetry logging in Postgres.
- **Security Boundary**: Loop iteration caps (`recursion_limit=50`), timeout guards, prompt injection sanitization, sandboxed tool dispatch.
- **Test Strategy**: Graph state transition validation, infinite loop termination tests, LLM timeout fallback tests, simulated agent crash recovery.

### Component 8: Classical Machine Learning & AutoML Engine
- **Purpose**: Automated algorithm discovery, baseline calculation, hyperparameter search, and model benchmarking for classification, regression, and clustering tasks.
- **Technology**: Scikit-Learn 1.9, XGBoost 3.4, LightGBM 4.7, Imbalanced-Learn 0.14, Optuna 5.0, SHAP 0.52.
- **Dependencies**: NumPy, SciPy, Pandas, Joblib.
- **Entry Point**: `backend/app/tools/model_trainer.py`, `backend/app/tools/ml_recommender.py`.
- **API**: Internal ML service tools and Celery/Redis background worker tasks.
- **Database Dependency**: Stores trial results, metrics, confusion matrices, and feature importances.
- **Security Boundary**: Strict separation of train/validation/test partitions before any preprocessing fit (anti-leakage guarantee); pickle/joblib deserialization restricted to internal trusted hash-verified paths.
- **Test Strategy**: Synthetic benchmark tests across balanced, imbalanced, skewed, and missing datasets; cross-validation fold stability tests; data leakage assertion checks.

### Component 9: Deep Learning Framework
- **Purpose**: Neural network architectures for high-dimensional tabular, sequence, and complex feature representations where classical algorithms saturate.
- **Technology**: PyTorch 2.14, TorchVision, Torch Audio (optional).
- **Dependencies**: CUDA (when available), CPU fallbacks.
- **Entry Point**: `backend/app/tools/deep_learning_tools/` and PyTorch model wrappers.
- **API**: PyTorch Module implementations integrated into the AutoML candidate search space.
- **Database Dependency**: Stores epoch histories, learning rate schedules, and loss curves.
- **Security Boundary**: Memory limits to prevent Out-Of-Memory (OOM) crashing the host; isolated tensor execution.
- **Test Strategy**: Tabular MLP verification, convergence check on non-linear synthetic classification, GPU vs CPU fallbacks.

### Component 10: Notebook & PDF Report Generation
- **Purpose**: Generation of auditable, standalone Jupyter Notebooks (`.ipynb`) reproducing the full pipeline from scratch, alongside executive PDF and Markdown reports.
- **Technology**: Jinja2 templating, ReportLab 5.0, Markdown 3.10, nbformat JSON schema.
- **Dependencies**: Python standard library `json`, Matplotlib chart exports.
- **Entry Point**: `backend/app/tools/notebook_generator.py`, `backend/app/tools/reporting/`.
- **API**: `/api/v1/sessions/{session_id}/reports/generate`.
- **Database Dependency**: Queries pipeline execution history, selected hyperparameters, and evaluation metrics.
- **Security Boundary**: Output redactor filters out API keys, database credentials, internal IPs, and local filesystem paths prior to PDF/IPYNB serialization.
- **Test Strategy**: Notebook execution validation (`nbconvert` / Python `exec`), PDF structural validity check, secret leak scan across generated artifacts.

### Component 11: Autonomous Self-Healing & Incident Recovery
- **Purpose**: Real-time error detection, categorization (transient vs permanent), exponential backoff retries, state rollback, and user-safe error masking.
- **Technology**: Custom recovery supervisor, Pydantic error models, Loguru diagnostic logger.
- **Dependencies**: `backend/recovery/` package.
- **Entry Point**: `backend/recovery/recovery_supervisor.py`, `backend/recovery/error_detector.py`.
- **API**: Global exception handler integration in `backend/main.py`.
- **Database Dependency**: Incident logs and recovery audit events stored in DB.
- **Security Boundary**: Guarantees zero raw stack traces or internal secrets leak to end users or clients during 500 errors.
- **Test Strategy**: Synthetic failure injection (DB down, Redis down, LLM timeout, malformed data), verification of safe masked error response and audit record generation.

### Component 12: Containerization & Deployment Orchestration
- **Purpose**: Production-grade multi-container topology orchestrating Web, API, Worker, Database, Redis, and Object Store with health checks and restart policies.
- **Technology**: Docker Compose v3.9, Docker multi-stage builds, Alpine base images, Nginx reverse proxy.
- **Dependencies**: Docker Engine 29+, Docker Compose v5+.
- **Entry Point**: `docker-compose.yml`, `docker/Dockerfile.backend`, `docker/Dockerfile.frontend`.
- **Security Boundary**: Non-root container users, isolated internal Docker network (`datawise_network`), read-only root filesystems where applicable, secrets passed via environment.
- **Test Strategy**: Docker Compose configuration lint, multi-stage build tests, container healthcheck validation, container networking isolation verification.

---

## 3. Global Architecture Security Boundaries

```
[ External Untrusted Internet ]
              │ (HTTPS / WSS)
              ▼
    [ Reverse Proxy / Nginx ]  ─── Rate Limiting & SSL Termination
              │ (HTTP Internal)
              ▼
    [ FastAPI API Gateway ]    ─── CORS, JWT Auth, Distributed Rate Limiter,
              │                     Input Validation (Pydantic), Output Security Gate
    ┌─────────┼───────────────────────────┐
    ▼         ▼                           ▼
[ PostgreSQL ] [ Redis Broker / Lock ]   [ S3 / MinIO Storage ]
 (Strict RLS)   (Isolated DB Index)       (Presigned Expiring URLs)
                      │
                      ▼
             [ Background Worker ]
             (LangGraph Multi-Agent,
              AutoML & Training Sandbox)
```

---

## 4. Comprehensive Test Strategy & Release Gates
1. **Static Analysis & Security**: ESLint, TypeScript compiler, Ruff/Flake8, Pyright, Secret Scanners, Pip-Audit, NPM Audit.
2. **Unit & Isolation Testing**: Preprocessing math, encoding, outlier detection, scaling, metric calculation, error normalization.
3. **Integration & API Contract Testing**: FastAPI TestClient end-to-end endpoints, session lifecycle, dataset CRUD, decision dispatch.
4. **Machine Learning Quality & Anti-Leakage Gates**: Strict train-test separation, cross-validation invariance, model artifact round-trip (`save -> load -> predict`).
5. **Agent Robustness & Boundary Testing**: Cycle termination, recursion limit defense, prompt injection immunity, tool argument schema validation.
6. **Infrastructure Resilience Testing**: Database disconnection recovery, Redis outage fallback, MinIO failure graceful handling.
7. **End-to-End Workflow Verification**: Multi-step user journey from raw CSV upload to deployed model and live prediction serving.
