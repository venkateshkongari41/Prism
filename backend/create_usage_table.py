from app.auth.database import get_connection


connection = get_connection()

connection.execute(
    """
    CREATE TABLE IF NOT EXISTS request_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER,
        application_name TEXT NOT NULL,
        model TEXT,
        provider TEXT,
        status TEXT NOT NULL,
        latency_ms REAL,
        created_at TEXT NOT NULL
    )
    """
)

connection.commit()
connection.close()

print("request_usage table created successfully")