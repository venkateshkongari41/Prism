from datetime import datetime, timedelta, timezone

from app.auth.database import get_connection


def record_usage(
    application_id: int | None,
    application_name: str,
    model: str | None,
    provider: str | None,
    status: str,
    latency_ms: float | None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    cost: float | None = None,
    request_id: str | None = None,
) -> int:

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO request_usage (
                application_id,
                application_name,
                model,
                provider,
                status,
                latency_ms,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost,
                created_at,
                request_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                application_id,
                application_name,
                model,
                provider,
                status,
                latency_ms,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost,
                created_at,
                request_id,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_usage(
    application_name: str | None = None,
    limit: int = 100,
) -> list[dict]:

    connection = get_connection()

    try:

        if application_name:

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
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    cost,
                    created_at
                FROM request_usage
                WHERE application_name = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    application_name,
                    limit,
                ),
            ).fetchall()

        else:

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
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    cost,
                    created_at
                FROM request_usage
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_usage_summary(
    application_name: str | None = None,
    hours: int | None = None,
) -> dict:

    connection = get_connection()

    try:

        conditions = []
        parameters = []

        if application_name:

            conditions.append(
                "application_name = ?"
            )

            parameters.append(
                application_name
            )

        if hours is not None:

            if hours <= 0:
                raise ValueError(
                    "hours must be greater than 0"
                )

            cutoff = (
                datetime.now(timezone.utc)
                - timedelta(hours=hours)
            ).isoformat()

            conditions.append(
                "created_at >= ?"
            )

            parameters.append(cutoff)

        where_clause = ""

        if conditions:

            where_clause = (
                "WHERE "
                + " AND ".join(conditions)
            )

        row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS total_requests,

                SUM(
                    CASE
                        WHEN status = 'success'
                        THEN 1
                        ELSE 0
                    END
                ) AS successful_requests,

                SUM(
                    CASE
                        WHEN status = 'failed'
                        THEN 1
                        ELSE 0
                    END
                ) AS failed_requests,

                COALESCE(
                    SUM(prompt_tokens),
                    0
                ) AS total_prompt_tokens,

                COALESCE(
                    SUM(completion_tokens),
                    0
                ) AS total_completion_tokens,

                COALESCE(
                    SUM(total_tokens),
                    0
                ) AS total_tokens,

                COALESCE(
                    SUM(cost),
                    0
                ) AS total_cost,

                COALESCE(
                    AVG(latency_ms),
                    0
                ) AS average_latency_ms

            FROM request_usage

            {where_clause}
            """,
            parameters,
        ).fetchone()

        return {
            "total_requests": row[
                "total_requests"
            ],
            "successful_requests": row[
                "successful_requests"
            ] or 0,
            "failed_requests": row[
                "failed_requests"
            ] or 0,
            "total_prompt_tokens": row[
                "total_prompt_tokens"
            ] or 0,
            "total_completion_tokens": row[
                "total_completion_tokens"
            ] or 0,
            "total_tokens": row[
                "total_tokens"
            ] or 0,
            "total_cost": float(
                row["total_cost"] or 0
            ),
            "average_latency_ms": float(
                row["average_latency_ms"] or 0
            ),
        }

    finally:
        connection.close()


def get_usage_by_application(
    hours: int | None = None,
) -> list[dict]:

    connection = get_connection()

    try:

        parameters = []
        where_clause = ""

        if hours is not None:

            if hours <= 0:
                raise ValueError(
                    "hours must be greater than 0"
                )

            cutoff = (
                datetime.now(timezone.utc)
                - timedelta(hours=hours)
            ).isoformat()

            where_clause = (
                "WHERE created_at >= ?"
            )

            parameters.append(cutoff)

        rows = connection.execute(
            f"""
            SELECT
                application_name,

                COUNT(*) AS total_requests,

                SUM(
                    CASE
                        WHEN status = 'success'
                        THEN 1
                        ELSE 0
                    END
                ) AS successful_requests,

                SUM(
                    CASE
                        WHEN status = 'failed'
                        THEN 1
                        ELSE 0
                    END
                ) AS failed_requests,

                COALESCE(
                    SUM(prompt_tokens),
                    0
                ) AS total_prompt_tokens,

                COALESCE(
                    SUM(completion_tokens),
                    0
                ) AS total_completion_tokens,

                COALESCE(
                    SUM(total_tokens),
                    0
                ) AS total_tokens,

                COALESCE(
                    SUM(cost),
                    0
                ) AS total_cost,

                COALESCE(
                    AVG(latency_ms),
                    0
                ) AS average_latency_ms

            FROM request_usage

            {where_clause}

            GROUP BY application_name

            ORDER BY total_requests DESC
            """,
            parameters,
        ).fetchall()

        return [
            {
                "application_name": row[
                    "application_name"
                ],
                "total_requests": row[
                    "total_requests"
                ],
                "successful_requests": row[
                    "successful_requests"
                ] or 0,
                "failed_requests": row[
                    "failed_requests"
                ] or 0,
                "total_prompt_tokens": row[
                    "total_prompt_tokens"
                ] or 0,
                "total_completion_tokens": row[
                    "total_completion_tokens"
                ] or 0,
                "total_tokens": row[
                    "total_tokens"
                ] or 0,
                "total_cost": float(
                    row["total_cost"] or 0
                ),
                "average_latency_ms": float(
                    row["average_latency_ms"] or 0
                ),
            }
            for row in rows
        ]

    finally:
        connection.close()