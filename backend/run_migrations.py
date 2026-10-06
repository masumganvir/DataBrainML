import asyncio
from app.db.session import engine
from sqlalchemy import text

statements = [
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

async def migrate():
    for stmt in statements:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(stmt))
            first_line = stmt.strip().split("\n")[0]
            print(f"SUCCESS: {first_line}")
        except Exception as e:
            print(f"FAILED: {stmt[:30]} => {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
