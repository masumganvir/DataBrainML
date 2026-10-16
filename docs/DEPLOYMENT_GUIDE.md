# DataWise AI — Production Deployment Guide

**Audience:** DevOps Engineers, Platform Administrators  
**Platform:** Ubuntu 22.04 LTS / Docker Compose / Kubernetes  

---

## 1. System Requirements

- **CPU:** 4 vCPUs minimum (8 vCPUs recommended for multi-tenant AutoML).
- **RAM:** 8 GB minimum (16 GB recommended).
- **Disk:** 50 GB NVMe SSD for models, datasets, and SQLite/PostgreSQL storage.
- **Python:** Python 3.11 - 3.14.
- **Node.js:** Node.js 18.x - 22.x.

---

## 2. Docker Compose Deployment

A turnkey `docker-compose.yml` is provided for containerized multi-service deployment:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: datawise
      POSTGRES_USER: datawise_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      DATABASE_URL: postgresql+asyncpg://datawise_user:${DB_PASSWORD}@db:5432/datawise
      JWT_SECRET: ${JWT_SECRET}
      FRONTEND_URL: ${FRONTEND_URL}
      ENVIRONMENT: production
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  pgdata:
```

---

## 3. Reverse Proxy (NGINX) & SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name datawise.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/datawise.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/datawise.yourdomain.com/privkey.pem;

    # Frontend Assets
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API & WebSocket
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }
}
```
