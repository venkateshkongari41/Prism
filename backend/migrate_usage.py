from app.auth.database import get_connection


connection = get_connection()

try:
    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(request_usage)"
        ).fetchall()
    }

    migrations = [
        (
            "prompt_tokens",
            """
            ALTER TABLE request_usage
            ADD COLUMN prompt_tokens INTEGER
            """,
        ),
        (
            "completion_tokens",
            """
            ALTER TABLE request_usage
            ADD COLUMN completion_tokens INTEGER
            """,
        ),
        (
            "total_tokens",
            """
            ALTER TABLE request_usage
            ADD COLUMN total_tokens INTEGER
            """,
        ),
        (
            "cost",
            """
            ALTER TABLE request_usage
            ADD COLUMN cost REAL
            """,
        ),
    ]

    for column_name, sql in migrations:

        if column_name not in columns:
            connection.execute(sql)
            print(
                f"Added column: {column_name}"
            )
        else:
            print(
                f"Column already exists: "
                f"{column_name}"
            )

    connection.commit()

finally:
    connection.close()