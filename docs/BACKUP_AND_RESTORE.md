# DataWise AI — Backup & Disaster Recovery Procedures

**Recovery Time Objective (RTO):** < 15 minutes  
**Recovery Point Objective (RPO):** < 1 hour  

---

## 1. Backup Strategy

### 1.1 Database Backups
- **PostgreSQL (Production):** Automated continuous WAL archiving with daily full physical dumps using `pg_dump`:
  ```bash
  pg_dump -Fc -h $DB_HOST -U $DB_USER -d datawise > /backups/datawise_$(date +%Y%m%d_%H%M%S).dump
  ```
- **SQLite (Development / Staging):** Atomic online backup via SQLite vacuum / backup API:
  ```bash
  sqlite3 datawise.db ".backup '/backups/datawise_$(date +%Y%m%d_%H%M%S).db'"
  ```

### 1.2 Object & Artifact Storage Backups
- Artifact directories (`artifacts/` or cloud storage buckets) should replicate continuously across multi-region object storage (e.g., AWS S3 Cross-Region Replication or Wasabi/Backblaze B2).

---

## 2. Restoration & Recovery Runbook

### Step 1: Halt Application Ingestion
Stop web workers to prevent partial write inconsistency during restore:
```bash
docker-compose stop backend
```

### Step 2: Restore Database Dump
```bash
# PostgreSQL
pg_restore -c -h $DB_HOST -U $DB_USER -d datawise /backups/datawise_target.dump

# SQLite
cp /backups/datawise_target.db ./datawise.db
```

### Step 3: Validate Database Integrity
Run schema integrity checks:
```bash
python backend/apply_sqlite_migrations.py
```

### Step 4: Resume Services & Verify
```bash
docker-compose up -d backend
curl -f http://localhost:8000/api/health
```
