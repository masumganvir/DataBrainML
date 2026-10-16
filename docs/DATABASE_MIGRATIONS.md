# DataWise AI — Database Migrations & Schema Evolution Guide

**Status:** AUTOMATED & ZERO-DOWNTIME COMPLIANT  
**Engines Supported:** SQLite (Local/Dev) & PostgreSQL 15+ (Production)  

---

## 1. Migration Philosophy & Safety Rules

1. **Non-Destructive Operations Only:** No migration script should drop existing tables or delete existing user datasets without explicit offline operator approval.
2. **Column Backfills:** New non-nullable columns must provide a deterministic default value or be created nullable initially.
3. **Automatic SQLite Synchronization:** The application incorporates startup reflection via `PRAGMA table_info` to detect missing columns on existing installations and issue `ALTER TABLE ADD COLUMN` statements atomically.

---

## 2. Executing Migrations

### Local / SQLite Migration Utility
To manually synchronize SQLite schemas without starting the full web service:
```bash
python backend/apply_sqlite_migrations.py
```

### Alembic (PostgreSQL) Migrations
For production PostgreSQL deployments:
```bash
# Generate a new revision
alembic revision --autogenerate -m "add_model_governance_columns"

# Apply pending revisions
alembic upgrade head

# Rollback single revision
alembic downgrade -1
```

---

## 3. Schema Version History

| Revision ID | Applied Columns / Tables | Description |
|---|---|---|
| `rev_001_initial` | `users`, `projects`, `datasets`, `runs` | Base data model for users, projects, and datasets. |
| `rev_002_prompts` | `project_prompts`, `prompt_versions` | Versioned AI prompt storage linked to projects. |
| `rev_003_artifacts`| `artifacts`, `models`, `evaluations` | Explicit linkage between runs, models, and artifacts. |
| `rev_004_slugs` | `projects.slug`, `projects.objective` | Route-friendly project slugs and high-level objectives. |
| `rev_005_audit` | `audit_logs` | Append-only security audit log table. |
