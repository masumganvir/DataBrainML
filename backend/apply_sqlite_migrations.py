"""DataWise AI — SQLite Safe Auto-Migration Utility
Ensures SQLite databases have all required columns from entities.py without data loss.
"""
import sqlite3
from pathlib import Path

def migrate_db(db_path: str):
    p = Path(db_path)
    if not p.exists():
        return
    print(f"Migrating {p.resolve()}...")
    conn = sqlite3.connect(p)
    cursor = conn.cursor()

    # 1. projects table
    cursor.execute("PRAGMA table_info(projects);")
    cols = {r[1] for r in cursor.fetchall()}
    if cols:
        add_cols = [
            ("slug", "VARCHAR(150)"),
            ("objective", "TEXT"),
            ("visibility", "VARCHAR(20) DEFAULT 'private'"),
            ("current_dataset_id", "VARCHAR(36)"),
            ("current_run_id", "VARCHAR(36)"),
            ("latest_model_id", "VARCHAR(36)"),
            ("latest_model_version", "VARCHAR(20)"),
            ("project_metadata", "TEXT DEFAULT '{}'"),
        ]
        for col_name, col_type in add_cols:
            if col_name not in cols:
                cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type};")
                print(f"  + Added column 'projects.{col_name}'")

    # 2. artifacts table
    cursor.execute("PRAGMA table_info(artifacts);")
    art_cols = {r[1] for r in cursor.fetchall()}
    if art_cols:
        add_art_cols = [
            ("user_id", "VARCHAR(36)"),
            ("run_id", "VARCHAR(36)"),
            ("dataset_id", "VARCHAR(36)"),
            ("version", "INTEGER DEFAULT 1"),
            ("artifact_name", "VARCHAR(255)"),
        ]
        for col_name, col_type in add_art_cols:
            if col_name not in art_cols:
                cursor.execute(f"ALTER TABLE artifacts ADD COLUMN {col_name} {col_type};")
                print(f"  + Added column 'artifacts.{col_name}'")

    # 3. users table
    cursor.execute("PRAGMA table_info(users);")
    user_cols = {r[1] for r in cursor.fetchall()}
    if user_cols:
        add_user_cols = [
            ("last_login_at", "TIMESTAMP"),
            ("deleted_at", "TIMESTAMP"),
        ]
        for col_name, col_type in add_user_cols:
            if col_name not in user_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
                print(f"  + Added column 'users.{col_name}'")

    conn.commit()
    conn.close()
    print(f"Migration completed for {p.name}.\n")

if __name__ == "__main__":
    for path in ["datawise.db", "../datawise.db", "datalab.db"]:
        migrate_db(path)
