"""
DataWise AI — Supabase Database Migration & Verification Utility
Connects to Supabase PostgreSQL and applies `supabase_master_schema.sql`.
"""

import asyncio
import os
import sys
from pathlib import Path
from loguru import logger

# Ensure root backend in path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings


async def run_supabase_migration():
    settings = get_settings()
    db_url = os.getenv("DATABASE_URL") or settings.database_url

    schema_file = Path(__file__).resolve().parent / "supabase_master_schema.sql"
    if not schema_file.exists():
        logger.error(f"Schema file not found at: {schema_file}")
        return False

    sql_content = schema_file.read_text(encoding="utf-8")

    logger.info(f"Target Database URL: {db_url[:25]}... (length={len(db_url)})")

    if "supabase.co" not in db_url and "postgres" not in db_url:
        logger.warning(
            "DATABASE_URL does not appear to point to Supabase or PostgreSQL. "
            "Please configure your Supabase DATABASE_URL in .env before running this script."
        )
        print("\n" + "=" * 70)
        print("HOW TO RUN THIS IN SUPABASE:")
        print("1. Log in to your Supabase Dashboard: https://supabase.com/dashboard")
        print("2. Open your project -> Click 'SQL Editor' in the left sidebar")
        print("3. Copy the entire contents of:")
        print(f"   {schema_file}")
        print("4. Paste into the SQL Editor and click 'Run'.")
        print("=" * 70 + "\n")
        return False

    try:
        import asyncpg
        import urllib.parse

        # Clean URL for asyncpg
        clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Prefer session pooler (port 5432) for DDL migrations
        if ":6543/" in clean_url:
            clean_url = clean_url.replace(":6543/", ":5432/")

        logger.info(f"Connecting to Supabase PostgreSQL at {clean_url.split('@')[1]}...")
        conn = await asyncpg.connect(clean_url, statement_cache_size=0)
        try:
            logger.info("Executing master Supabase schema, triggers, and RLS policies...")
            await conn.execute(sql_content)
            logger.success("Supabase schema, triggers, and RLS policies successfully applied!")
            return True
        finally:
            await conn.close()
    except Exception as exc:
        logger.error(f"Migration error: {exc}")
        print("\nTip: You can also copy-paste the SQL directly in the Supabase Dashboard -> SQL Editor.")
        return False


if __name__ == "__main__":
    asyncio.run(run_supabase_migration())
