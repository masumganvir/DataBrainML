FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source trees
COPY . .

# Create persistent storage directories
RUN mkdir -p data/uploads artifacts/models artifacts/plots artifacts/reports artifacts/notebooks logs

# Create non-root application user for container security
RUN adduser --disabled-password --gecos "" datawise && \
    chown -R datawise:datawise /app
USER datawise

EXPOSE 8000

ENV PYTHONPATH="/app:/app/backend"
CMD ["uvicorn", "backend.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
