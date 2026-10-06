from app.auth.database import get_connection


connection = get_connection()

try:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'request_usage'
        """
    ).fetchone()

    if row:
        print(row["sql"])
    else:
        print("request_usage table not found")

finally:
    connection.close()