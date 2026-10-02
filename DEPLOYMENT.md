# Deployment, Containerization & Operations Guide

## 1. Local Development
```powershell
# Clone and enter directory
cd backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run migrations
python -m alembic upgrade head

# Start API
uvicorn main:app --reload --port 8000
```

## 2. Docker Compose Deployment
```bash
# Start all production infrastructure
docker compose up -d --build

# Inspect running services
docker compose ps

# Check logs
docker compose logs -f backend worker
```

## 3. Kubernetes-Ready Container Specifications
Containers are built as unprivileged stateless units:
- `backend`: Exposes port 8000, runs Uvicorn ASGI workers.
- `worker`: Runs asynchronous LangGraph agent jobs pulled from Redis queues.
- `postgres`: Persistent volume `postgres_data`.
- `redis`: In-memory caching with append-only file persistence.
- `minio`: S3-compatible storage cluster with `/data` volume.

## 4. Environment Checklist
Ensure `.env` contains:
- `DATABASE_URL` pointing to PostgreSQL cluster
- `REDIS_URL` pointing to Redis cluster
- `S3_ENDPOINT` and bucket configuration
- `SECRET_KEY` (minimum 32-character random string)
- `LLM_PROVIDER` and API keys
