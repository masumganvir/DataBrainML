# Database Backup, Disaster Recovery & Retention Policy

## 1. Backup Strategy
- **Daily Full Logical Backups**: Automated `pg_dump` compressed snapshot taken at 02:00 UTC.
- **Continuous Archiving / Point-In-Time Recovery (PITR)**: Write-Ahead Logs (`WAL`) archived to secondary object storage.
- **RPO (Recovery Point Objective)**: < 15 minutes.
- **RTO (Recovery Time Objective)**: < 30 minutes.

## 2. Backup Execution
```bash
# Automated database backup script
pg_dump -h localhost -U datawise -d datawise_db -F c -b -v -f "/backups/datawise_$(date +%Y%m%d_%H%M%S).dump"
```

## 3. Disaster Recovery & Restoration Procedure
```bash
# Terminate existing active sessions
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'datawise_db' AND pid <> pg_backend_pid();

# Drop and recreate target database
DROP DATABASE datawise_db;
CREATE DATABASE datawise_db OWNER datawise;

# Restore from snapshot
pg_restore -h localhost -U datawise -d datawise_db -v "/backups/datawise_snapshot.dump"
```

## 4. Retention Policy
- Database snapshots: 30 days daily, 12 months monthly.
- Prediction requests: Configurable 90 days retention with auto-pruning.
- Production model artifacts: Retained indefinitely in cold storage (WORM compliance: Write Once, Read Many).
