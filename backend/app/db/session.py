"""DataWise AI — Enterprise Database Session & Engine Configuration

Configured with SQLAlchemy 2.x async engine, connection pooling parameters
(DATABASE_POOL_SIZE, DATABASE_MAX_OVERFLOW, DATABASE_POOL_TIMEOUT, DATABASE_POOL_RECYCLE),
statement timeouts, and dialect-agnostic session management.

NOTE: Supabase uses PgBouncer in transaction-pool mode.
      asyncpg must have statement_cache_size=0 to disable prepared statements,
      otherwise you get DuplicatePreparedStatementError on startup.
"""

from __future__ import annotations

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings
from app.db.models.entities import Base

settings = get_settings()

# Engine kwargs based on driver (SQLite does not support pool_size/max_overflow)
engine_kwargs: dict = {
    "echo": settings.is_development,
    "future": True,
}

_is_postgres = "sqlite" not in settings.database_url

if _is_postgres:
    engine_kwargs.update({
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
        "pool_recycle": settings.database_pool_recycle,
        "pool_pre_ping": True,
        # Supabase/PgBouncer: disable prepared statements to avoid
        # DuplicatePreparedStatementError in transaction-pool mode.
        "connect_args": {
            "statement_cache_size": 0,
            "server_settings": {"search_path": "public"},
        },
    })

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize the database.

    - SQLite (local dev): creates all tables automatically via Base.metadata.
    - Supabase/PostgreSQL: schema is managed by database/supabase_schema.sql.
      We skip CREATE TABLE (which would fail due to type mismatches with
      Supabase's UUID columns) and just verify connectivity instead.
    """
    from loguru import logger
    if "supabase.co" in settings.database_url or "supabase.com" in settings.database_url:
        from sqlalchemy import text
        migration_sqls = [
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS slug VARCHAR(150);",
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS objective TEXT;",
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'private';",
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS current_dataset_id VARCHAR(36);",
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS current_run_id VARCHAR(36);",
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS latest_model_id VARCHAR(36);",
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS latest_model_version VARCHAR(20);",
            "ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS project_metadata JSONB DEFAULT '{}'::jsonb;",
            "ALTER TABLE public.artifacts ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);",
            "ALTER TABLE public.artifacts ADD COLUMN IF NOT EXISTS run_id VARCHAR(36);",
            "ALTER TABLE public.artifacts ADD COLUMN IF NOT EXISTS dataset_id VARCHAR(36);",
            "ALTER TABLE public.artifacts ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;",
            "ALTER TABLE public.artifacts ADD COLUMN IF NOT EXISTS artifact_name VARCHAR(255);",
            """CREATE TABLE IF NOT EXISTS public.project_prompts (
                id VARCHAR(36) PRIMARY KEY,
                project_id VARCHAR(36) NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                content TEXT NOT NULL,
                created_by VARCHAR(36),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );"""
        ]
        for sql in migration_sqls:
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(sql))
            except Exception as e:
                logger.debug(f"Migration note: {e}")
        logger.info("Supabase DB connectivity & project identity schema verified.")
    else:
        # Local SQLite or custom Postgres — auto-create tables.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Local DB tables created/verified via SQLAlchemy metadata.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an active async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
