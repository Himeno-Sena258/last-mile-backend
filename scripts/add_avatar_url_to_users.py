"""
迁移脚本：为 users 表添加 avatar_url 列
支持方言：PostgreSQL、MySQL/MariaDB、SQLite（3.35+）
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine

# Ensure project root is on sys.path to import app.*
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.models.user import User

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

SQLS = {
    "postgresql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);",
    "mysql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);",
    "mariadb": "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);",
    "sqlite": "ALTER TABLE users ADD COLUMN avatar_url TEXT;",
}


def get_dialect_name(engine: Engine) -> str:
    name = engine.dialect.name
    if name == "postgresql":
        return "postgresql"
    if name in ("mysql", "mariadb"):
        return name
    if name == "sqlite":
        return "sqlite"
    return name


def table_exists(engine: Engine, table: str) -> bool:
    insp = inspect(engine)
    try:
        return insp.has_table(table)
    except Exception:
        # Fallback for unusual dialects
        with engine.connect() as conn:
            try:
                conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                return True
            except Exception:
                return False


def column_exists(engine: Engine, table: str, column: str) -> bool:
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            result = conn.execute(text(f"PRAGMA table_info({table});")).fetchall()
            cols = [row[1] for row in result]
            return column in cols
        else:
            result = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = :table AND column_name = :column
                    """
                ),
                {"table": table, "column": column},
            ).scalar()
            return bool(result)


def main():
    engine = create_engine(DATABASE_URL)
    dialect = get_dialect_name(engine)

    # Create users table if missing (will include avatar_url per model)
    if not table_exists(engine, "users"):
        print("Table 'users' does not exist. Creating it using SQLAlchemy models...")
        User.__table__.create(bind=engine, checkfirst=True)
        print("Created 'users' table.")
        return

    # Skip if column already exists
    if column_exists(engine, "users", "avatar_url"):
        print("Column 'avatar_url' already exists in 'users'. Skipping.")
        return

    sql = SQLS.get(dialect)
    if not sql:
        raise RuntimeError(f"Unsupported database dialect: {dialect}")

    with engine.begin() as conn:
        conn.execute(text(sql))
        print("Added column 'avatar_url' to 'users' table.")


if __name__ == "__main__":
    main()