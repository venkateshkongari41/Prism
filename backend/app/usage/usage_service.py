from datetime import datetime, timedelta, timezone

from app.auth.database import get_connection


def _ensure_request_usage_columns(connection) -> None:
    """
    Add request-log columns introduced after the original schema.

    This keeps existing SQLite databases compatible without requiring
    a destructive migration.
    """

    rows = connection.execute(
        "PRAGMA table_info(request_usage)"
    ).fetchall()

    columns = {
        row["name"]
        for row in rows
    }

    if "cache_type" not in columns:
        connection.execute(
            """
            ALTER TABLE request_usage
            ADD COLUMN cache_type TEXT
            """
        )

    if "fallback_used" not in columns:
        connection.execute(
            """
            ALTER TABLE request_usage
            ADD COLUMN fallback_used INTEGER NOT NULL DEFAULT 0
            """
        )


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
    cache_type: str | None = None,
    fallback_used: bool = False,
) -> int:

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:

        _ensure_request_usage_columns(
            connection
        )

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
                request_id,
                cache_type,
                fallback_used
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
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
                cache_type,
                int(bool(fallback_used)),
            ),
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_usage(
    application_name: str | None = None,
    limit: int = 100,
    hours: int | None = None,
) -> list[dict]:

    connection = get_connection()

    try:

        _ensure_request_usage_columns(connection)

        conditions = []
        parameters = []

        if application_name:
            conditions.append("application_name = ?")
            parameters.append(application_name)

        if hours is not None:
            if hours <= 0:
                raise ValueError(
                    "hours must be greater than 0"
                )

            cutoff = (
                datetime.now(timezone.utc)
                - timedelta(hours=hours)
            ).isoformat()

            conditions.append("created_at >= ?")
            parameters.append(cutoff)

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE "
                + " AND ".join(conditions)
            )

        query = f"""
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
                created_at,
                request_id,
                cache_type,
                fallback_used
            FROM request_usage
            {where_clause}
            ORDER BY id DESC
            LIMIT ?
        """

        parameters.append(limit)

        rows = connection.execute(
            query,
            tuple(parameters),
        ).fetchall()

        result = []

        for row in rows:
            item = dict(row)
            item["fallback_used"] = bool(
                item["fallback_used"]
            )
            result.append(item)

        return result

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
                datetime.now(
                    timezone.utc
                )
                - timedelta(hours=hours)
            ).isoformat()

            conditions.append(
                "created_at >= ?"
            )

            parameters.append(
                cutoff
            )

        where_clause = ""

        if conditions:

            where_clause = (
                "WHERE "
                + " AND ".join(
                    conditions
                )
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
                ) AS average_latency_ms,

                SUM(
                    CASE
                        WHEN cache_type IN ('exact', 'semantic')
                        THEN 1
                        ELSE 0
                    END
                ) AS cache_hits,

                SUM(
                    CASE
                        WHEN cache_type = 'miss'
                        THEN 1
                        ELSE 0
                    END
                ) AS cache_misses,

                SUM(
                    CASE
                        WHEN fallback_used = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS fallback_requests

            FROM request_usage

            {where_clause}
            """,
            parameters,
        ).fetchone()

        breakdown_rows = connection.execute(
            f"""
            SELECT
                model,
                provider,
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
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(cost), 0) AS total_cost
            FROM request_usage
            {where_clause}
            GROUP BY model, provider
            ORDER BY total_requests DESC, model, provider
            """,
            parameters,
        ).fetchall()

        return {
            "total_requests": row[
                "total_requests"
            ],
            "successful_requests": row[
                "successful_requests"
            ]
            or 0,
            "failed_requests": row[
                "failed_requests"
            ]
            or 0,
            "total_prompt_tokens": row[
                "total_prompt_tokens"
            ]
            or 0,
            "total_completion_tokens": row[
                "total_completion_tokens"
            ]
            or 0,
            "total_tokens": row[
                "total_tokens"
            ]
            or 0,
            "total_cost": float(
                row["total_cost"] or 0
            ),
            "average_latency_ms": float(
                row["average_latency_ms"] or 0
            ),
            "cache_hits": row["cache_hits"] or 0,
            "cache_misses": row["cache_misses"] or 0,
            "cache_hit_rate": (
                (row["cache_hits"] or 0)
                / (
                    (row["cache_hits"] or 0)
                    + (row["cache_misses"] or 0)
                )
                if (
                    (row["cache_hits"] or 0)
                    + (row["cache_misses"] or 0)
                ) > 0
                else 0.0
            ),
            "fallback_requests": row["fallback_requests"] or 0,
            "model_provider_breakdown": [
                {
                    "model": breakdown["model"],
                    "provider": breakdown["provider"],
                    "total_requests": breakdown["total_requests"],
                    "successful_requests": (
                        breakdown["successful_requests"] or 0
                    ),
                    "failed_requests": (
                        breakdown["failed_requests"] or 0
                    ),
                    "total_tokens": breakdown["total_tokens"],
                    "total_cost": float(
                        breakdown["total_cost"] or 0
                    ),
                }
                for breakdown in breakdown_rows
            ],
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
                datetime.now(
                    timezone.utc
                )
                - timedelta(hours=hours)
            ).isoformat()

            where_clause = (
                "WHERE created_at >= ?"
            )

            parameters.append(
                cutoff
            )

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
                ) AS average_latency_ms,

                SUM(
                    CASE
                        WHEN cache_type IN ('exact', 'semantic')
                        THEN 1
                        ELSE 0
                    END
                ) AS cache_hits,

                SUM(
                    CASE
                        WHEN cache_type = 'miss'
                        THEN 1
                        ELSE 0
                    END
                ) AS cache_misses,

                SUM(
                    CASE
                        WHEN fallback_used = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS fallback_requests

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
                ]
                or 0,
                "failed_requests": row[
                    "failed_requests"
                ]
                or 0,
                "total_prompt_tokens": row[
                    "total_prompt_tokens"
                ]
                or 0,
                "total_completion_tokens": row[
                    "total_completion_tokens"
                ]
                or 0,
                "total_tokens": row[
                    "total_tokens"
                ]
                or 0,
                "total_cost": float(
                    row["total_cost"] or 0
                ),
                "average_latency_ms": float(
                    row["average_latency_ms"]
                    or 0
                ),
                "cache_hits": row["cache_hits"] or 0,
                "cache_misses": row["cache_misses"] or 0,
                "cache_hit_rate": (
                    (row["cache_hits"] or 0)
                    / (
                        (row["cache_hits"] or 0)
                        + (row["cache_misses"] or 0)
                    )
                    if (
                        (row["cache_hits"] or 0)
                        + (row["cache_misses"] or 0)
                    ) > 0
                    else 0.0
                ),
                "fallback_requests": row["fallback_requests"] or 0,
            }
            for row in rows
        ]

    finally:
        connection.close()