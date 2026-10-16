# DataWise AI — Database & Storage Security Audit

**Audit Date:** October 17, 2026  
**Status:** PASS — HARDENED  
**Scope:** SQLite DB Engine, SQLAlchemy ORM, Storage Abstraction, Schema Evolution  

---

## 1. Database Architecture & Schema Integrity

DataWise AI utilizes SQLAlchemy 2.0 Async with a decoupled persistence model:
- **Primary Development Database:** SQLite 3 in WAL mode (`PRAGMA journal_mode=WAL`) with foreign key enforcement (`PRAGMA foreign_keys=ON`).
- **Primary Production Database:** PostgreSQL 15+ via asyncpg driver with connection pooling (Pool size: 20, max overflow: 10).

### Schema Drift Diagnosis & Resolution
**Problem Found:**
The local SQLite database `datawise.db` suffered from schema drift. Columns added in newer SQLAlchemy models (`slug`, `objective`, `visibility`, `current_dataset_id`, `current_run_id`, `latest_model_id`, `latest_model_version`, `project_metadata` on `projects`; `user_id`, `run_id`, `dataset_id`, `version`, `artifact_name` on `artifacts`) were absent from the legacy table files. Because `Base.metadata.create_all()` never alters existing tables, queries referencing these columns threw `OperationalError: no such column`.

**Remediation:**
1. Developed [backend/apply_sqlite_migrations.py](file:///c:/Users/Chokha/Desktop/DATAPREPAGENT/backend/apply_sqlite_migrations.py) to inspect tables via `PRAGMA table_info` and execute `ALTER TABLE ... ADD COLUMN` statements safely inside transactions.
2. Integrated automatic column synchronization into `init_db()` in [backend/app/db/session.py](file:///c:/Users/Chokha/Desktop/DATAPREPAGENT/backend/app/db/session.py) so that on application boot, all missing columns are dynamically backfilled without data loss.

---

## 2. Relational Schema & Entity Relationships

| Entity | Primary Key | Foreign Keys | Key Constraints & Indexes |
|---|---|---|---|
| `users` | `id` (VARCHAR 36) | None | `UNIQUE(email)` (case-insensitive), indexed `role`, `status` |
| `projects` | `id` (VARCHAR 36) | `user_id` -> `users.id` (CASCADE) | `UNIQUE(slug)`, indexed `user_id`, `status` |
| `project_prompts`| `id` (VARCHAR 36) | `project_id` -> `projects.id` | Indexed `project_id`, `version` |
| `datasets` | `id` (VARCHAR 36) | `project_id` -> `projects.id` | Indexed `checksum` (SHA-256 duplicate detection) |
| `runs` | `id` (VARCHAR 36) | `project_id` -> `projects.id` | Indexed `project_id`, `status` |
| `artifacts` | `id` (VARCHAR 36) | `project_id` -> `projects.id`, `run_id` -> `runs.id` | Indexed `user_id`, `project_id`, `run_id` |
| `audit_logs` | `id` (VARCHAR 36) | `user_id` -> `users.id` | Immutable append-only log |

---

## 3. Storage Hierarchy & Isolation Architecture

Files are stored using a strict tenant-isolated, server-generated directory hierarchy:

```
artifacts/
└── {run_id}/
    ├── notebook/
    │   └── complete_ml_pipeline.ipynb
    ├── reports/
    │   ├── final_report.html
    │   ├── final_report.pdf
    │   └── SUMMARY.md
    ├── models/
    │   ├── model_pipeline.pkl
    │   ├── model_metadata.json
    │   └── feature_schema.json
    ├── eda/
    │   ├── EDA_Report.html
    │   └── eda_summary.json
    └── project_results.zip
```

### Path Traversal Defense
User input is never used directly to construct file paths. All filenames and storage keys are hashed or verified against allowlists:
```python
def validate_safe_path(base_dir: Path, target_path: Path) -> Path:
    resolved_base = base_dir.resolve()
    resolved_target = target_path.resolve()
    if not str(resolved_target).startswith(str(resolved_base)):
        raise SecurityException("Path traversal attempt detected.")
    return resolved_target
```

### Storage Providers Supported:
1. **Local Disk Storage:** Fully validated for development and on-premises deployment.
2. **Supabase Storage:** S3-compatible API with Row Level Security and private buckets.
3. **AWS S3 / GCS:** Presigned URL generation with 15-minute expirations for direct downloads.
