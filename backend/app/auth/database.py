import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

DATABASE_PATH = DATA_DIR / "prism.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                application_name TEXT NOT NULL DEFAULT 'default',

                key_hash TEXT NOT NULL UNIQUE,
                key_prefix TEXT NOT NULL,

                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,

                rate_limit INTEGER NOT NULL DEFAULT 60,
                rate_window_seconds INTEGER NOT NULL DEFAULT 60,

                allowed_models TEXT NOT NULL DEFAULT '*',

                monthly_budget REAL NOT NULL DEFAULT 0,
                monthly_spend REAL NOT NULL DEFAULT 0,
                budget_month TEXT
            )
            """
        )

        columns = connection.execute(
            """
            PRAGMA table_info(api_keys)
            """
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        migrations = {
            "application_name": """
                ALTER TABLE api_keys
                ADD COLUMN application_name
                TEXT NOT NULL DEFAULT 'default'
            """,

            "rate_limit": """
                ALTER TABLE api_keys
                ADD COLUMN rate_limit
                INTEGER NOT NULL DEFAULT 60
            """,

            "rate_window_seconds": """
                ALTER TABLE api_keys
                ADD COLUMN rate_window_seconds
                INTEGER NOT NULL DEFAULT 60
            """,

            "allowed_models": """
                ALTER TABLE api_keys
                ADD COLUMN allowed_models
                TEXT NOT NULL DEFAULT '*'
            """,

            "monthly_budget": """
                ALTER TABLE api_keys
                ADD COLUMN monthly_budget
                REAL NOT NULL DEFAULT 0
            """,

            "monthly_spend": """
                ALTER TABLE api_keys
                ADD COLUMN monthly_spend
                REAL NOT NULL DEFAULT 0
            """,

            "budget_month": """
                ALTER TABLE api_keys
                ADD COLUMN budget_month
                TEXT
            """,
        }

        for column_name, migration_sql in migrations.items():

            if column_name not in column_names:
                connection.execute(migration_sql)

        connection.commit()

    finally:
        connection.close()