# Redis Architecture & Distributed State

## 1. Purpose
Redis serves as the low-latency distributed state store, caching layer, and synchronization engine for DataWise AI across horizontal replicas. Redis is never used as the permanent source of truth; all authoritative records persist in PostgreSQL.

## 2. Architectural Responsibilities
- **Distributed Rate Limiting**: Atomic sliding-window counters via Lua scripts.
- **Distributed Concurrency Locks**: Preventing duplicate expensive operations (`lock:dataset:{id}:processing`, `lock:experiment:{id}:training`).
- **Deterministic Result Caching**: Schema summaries, profiles, model metadata with TTL.
- **Job Queues**: Priority lists (`queue:high`, `queue:default`, `queue:expensive`).
- **Idempotency Keys**: Short-lived request tokens (`idempotency:{token}`).
- **Real-Time Job Telemetry**: Real-time worker status keys (`job:status:{id}`).

## 3. Configuration
- `REDIS_URL`: `redis://redis:6379/0`
- `REDIS_PASSWORD`: Optional authentication secret
- Persistence: Append-Only File (`AOF`) enabled in Docker Compose.

## 4. Failure Scenarios & Recovery
- **Network Partition**: Connection manager implements `socket_connect_timeout=2.0s`. If Redis is unreachable, the system gracefully operates on a thread-safe `InMemoryFallbackCache`.
- **Lock Deadlock Prevention**: All distributed locks have a hard TTL (default 120s) and unique UUID tokens to prevent accidental eviction by other workers.

## 5. Production Considerations
- Enable Redis Sentinel or Redis Cluster in multi-region cloud deployments.
- Monitor memory usage with `maxmemory-policy volatile-lru`.
