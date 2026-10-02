# Security, Authentication & Role-Based Access Control (RBAC)

## 1. Purpose
Enforces defense-in-depth principles across authentication, authorization, secret protection, cryptographic integrity, and data safety.

## 2. Authentication & Credential Storage
- **Passwords**: Salted and hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations. Raw passwords are never persisted.
- **API Keys**: Issued with `dw_live_` prefixes. Raw tokens are shown to users only upon generation. The database stores `key_prefix` (for lookup) and `key_hash` (SHA-256).
- **JWT Tokens**: Signed with HS256 algorithm, verified on every protected request.

## 3. Role-Based Access Control (RBAC)
Role hierarchy:
- `owner`: Full organizational and project administration.
- `admin`: User management and project control.
- `developer`: Model building, dataset operations, code access.
- `data_scientist`: Exploration, training, tuning, and model promotion.
- `viewer`: Read-only access to datasets, plots, and reports.

Granular permissions:
`dataset.read`, `dataset.write`, `experiment.run`, `model.read`, `model.train`, `model.promote`, `deployment.create`, `deployment.manage`, `audit.read`.

## 4. Query Safety & SQL Injection Defense
All database interactions strictly utilize SQLAlchemy 2.0 ORM expressions and parameterized prepared statements. String concatenation of SQL queries is strictly prohibited.

## 5. Append-Only Audit Logging
Critical actions are recorded in the `audit_logs` table:
`login`, `logout`, `dataset_upload`, `model_training`, `model_promotion`, `deployment`, `rollback`, `api_key_creation`.
Audit records cannot be updated or soft deleted.
