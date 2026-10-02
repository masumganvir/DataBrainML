# Production Database Architecture (PostgreSQL & SQLAlchemy 2.x)

## 1. Purpose
PostgreSQL serves as the single source of truth for the entire DataWise AI Platform. It stores all transactional, relational, catalog, and audit records with strict consistency, referential integrity, and ACID guarantees. Large binary payloads (raw datasets, serialized ML model weights, charts, and PDFs) are never stored in PostgreSQL; instead, PostgreSQL stores structured metadata, checksums, and storage keys pointing to object storage.

## 2. Architecture & Schemas
The database uses SQLAlchemy 2.0 declarative models with async driver (`asyncpg` for production, `aiosqlite` for local dev tests).

### Logical Domain Entities (37 Tables)
1. **Identity & Auth**: `users`, `user_sessions`, `api_keys`.
2. **Workspaces & Tenancy**: `projects` (multi-tenant ready with `organization_id`).
3. **Data Lineage**: `datasets`, `dataset_versions` (immutable snapshots), `dataset_columns` (type profiles & missing stats), `dataset_profiles`, `data_quality_reports`.
4. **ML Experimentation**: `experiments`, `experiment_runs`, `preprocessing_runs`, `features`.
5. **Model Training & Metrics**: `model_candidates`, `training_runs`, `model_metrics`, `cross_validation_results`, `hyperparameter_runs` (Optuna trials).
6. **Diagnostics & Explanations**: `evaluation_results`, `overfitting_reports`, `explainability_results` (SHAP), `robustness_results`.
7. **Model Registry**: `models`, `model_versions` (immutable staging/production promotion, unique `model_id + version`).
8. **Artifacts & Generation**: `artifacts`, `notebooks`, `reports`.
9. **Inference & Observability**: `deployments` (dev/staging/prod), `prediction_requests` (telemetry, input hashes), `monitoring_metrics`, `drift_reports`.
10. **Agent Observability**: `agent_runs`, `agent_events`.
11. **Human-in-the-Loop Traceability**: `user_decisions` (records user overrides for imputations, outlier actions, training approvals).
12. **Security & Operations**: `audit_logs` (append-only), `jobs` (Redis worker tasks), `usage_records` (billing tokens).

### Indexing Strategy
- Composite B-Tree indexes: `(project_id, status)`, `(experiment_id, status)`, `(training_run_id, metric_name, dataset_split)`.
- Unique constraints: `email`, `(dataset_id, version)`, `(model_id, version)`.
- Foreign key cascading: child resources cascade on delete, audit logs use `SET NULL` on user deletion to preserve history.

## 3. Configuration & Connection Pooling
Configured through environment variables:
- `DATABASE_URL`: `postgresql+asyncpg://datawise:datawise_pass@postgres:5432/datawise_db`
- `DATABASE_POOL_SIZE`: 10 (base persistent connections)
- `DATABASE_MAX_OVERFLOW`: 20 (surge connections during spikes)
- `DATABASE_POOL_TIMEOUT`: 30s
- `DATABASE_POOL_RECYCLE`: 1800s (recycles stale connections)
- `DATABASE_STATEMENT_TIMEOUT`: 60000ms (prevents runaway long transactions)

## 4. Failure Scenarios & Recovery
- **Connection Saturation**: When max pool overflow is reached, requests queue up to `pool_timeout` (30s) before raising HTTP 503. Handled via application readiness probe.
- **Failover / Restart**: Async engine configured with `pool_pre_ping=True` to immediately disconnect dead sockets and reconnect on next acquire.

## 5. Production Considerations
- Never connect with the PostgreSQL `postgres` superuser. Use a restricted application user `datawise`.
- Keep ML model training calculations out of PostgreSQL transactions. Training runs asynchronously; database records are updated only on status transitions.
