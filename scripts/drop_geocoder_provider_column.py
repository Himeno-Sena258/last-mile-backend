import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect


def main():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set in environment")
        return 1

    engine = create_engine(database_url)
    insp = inspect(engine)

    has_tasks = insp.has_table("tasks")
    if not has_tasks:
        print("OK: table 'tasks' does not exist; nothing to migrate")
        return 0

    columns = [c['name'] for c in insp.get_columns('tasks')]
    if 'geocoder_provider' not in columns:
        print("OK: column 'geocoder_provider' already absent")
        return 0

    dialect = engine.dialect.name
    drop_sql = None

    if dialect == 'postgresql':
        drop_sql = "ALTER TABLE tasks DROP COLUMN IF EXISTS geocoder_provider;"
    elif dialect in ('mysql', 'mariadb'):
        drop_sql = "ALTER TABLE tasks DROP COLUMN geocoder_provider;"
    else:
        # Attempt SQLite 3.35+ DROP COLUMN
        drop_sql = "ALTER TABLE tasks DROP COLUMN geocoder_provider;"

    try:
        with engine.begin() as conn:
            conn.execute(text(drop_sql))
        # verify
        insp = inspect(engine)
        columns_after = [c['name'] for c in insp.get_columns('tasks')]
        if 'geocoder_provider' in columns_after:
            print("ERROR: column 'geocoder_provider' still present after DROP; manual migration may be required for this dialect")
            return 2
        print("OK: dropped column 'geocoder_provider' from 'tasks'")
        return 0
    except Exception as e:
        print(f"ERROR: failed to drop column: {e}")
        if dialect == 'sqlite':
            print("Hint: For SQLite <3.35, DROP COLUMN is unsupported; requires table recreation.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())