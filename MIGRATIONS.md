# Database Migrations with Alembic

## 1. Migration Protocol
Direct manual modifications of database schema in production environments are strictly prohibited. Every schema modification must follow the formal Alembic migration workflow.

## 2. Generating Migrations
```powershell
cd backend

# Auto-generate migration from ORM model changes
python -m alembic revision --autogenerate -m "add_drift_detection_columns"
```

## 3. Applying Migrations
```powershell
# Upgrade to latest head
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1

# Inspect current revision status
python -m alembic current
```

## 4. Migration Testing Procedure
1. Apply upgrade on test/staging PostgreSQL instance.
2. Run database integrity test suite (`pytest tests/test_production_database.py`).
3. Verify downgrade script on test instance.
4. Promote migration into CI/CD release pipeline.
