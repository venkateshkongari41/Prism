from app.auth.database import get_connection


def test_api_key_has_rate_limit_columns():

    connection = get_connection()

    try:
        columns = connection.execute(
            "PRAGMA table_info(api_keys)"
        ).fetchall()

        column_names = {
            row["name"]
            for row in columns
        }

        assert "rate_limit" in column_names
        assert (
            "rate_window_seconds"
            in column_names
        )

    finally:
        connection.close()