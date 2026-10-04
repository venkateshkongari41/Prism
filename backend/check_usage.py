from app.auth.database import get_connection


connection = get_connection()

rows = connection.execute(
    """
    SELECT
        id,
        application_id,
        application_name,
        model,
        provider,
        status,
        latency_ms,
        created_at
    FROM request_usage
    ORDER BY id DESC
    LIMIT 10
    """
).fetchall()

print("Recent usage records:")

for row in rows:
    print(dict(row))

connection.close()