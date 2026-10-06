import hashlib
import json
import secrets
from datetime import datetime, timezone

from app.auth.database import get_connection


KEY_PREFIX = "prism_live_"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()


def generate_api_key() -> str:
    random_part = secrets.token_urlsafe(32)

    return f"{KEY_PREFIX}{random_part}"


def current_budget_month() -> str:
    return datetime.now(
        timezone.utc
    ).strftime("%Y-%m")


def create_api_key(
    name: str,
    application_name: str,
    allowed_models: list[str] | None = None,
    monthly_budget: float = 0,
    rate_limit: int = 60,
    rate_window_seconds: int = 60,
) -> str:

    api_key = generate_api_key()

    key_hash = hash_api_key(api_key)

    key_prefix = api_key[:16]

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    if not allowed_models:
        allowed_models_value = "*"
    else:
        allowed_models_value = json.dumps(
            allowed_models
        )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO api_keys (
                name,
                application_name,
                key_hash,
                key_prefix,
                is_active,
                created_at,
                rate_limit,
                rate_window_seconds,
                allowed_models,
                monthly_budget,
                monthly_spend,
                budget_month
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                application_name,
                key_hash,
                key_prefix,
                1,
                created_at,
                rate_limit,
                rate_window_seconds,
                allowed_models_value,
                monthly_budget,
                0,
                current_budget_month(),
            ),
        )

        connection.commit()

    finally:
        connection.close()

    return api_key


def _parse_allowed_models(
    value: str | None,
) -> list[str]:

    if not value or value == "*":
        return ["*"]

    try:
        models = json.loads(value)

        if isinstance(models, list):
            return models

    except json.JSONDecodeError:
        pass

    return [
        model.strip()
        for model in value.split(",")
        if model.strip()
    ]


def _reset_monthly_budget_if_needed(
    connection: object,
    row: object,
) -> None:

    current_month = current_budget_month()

    budget_month = row["budget_month"]

    if budget_month != current_month:

        connection.execute(
            """
            UPDATE api_keys
            SET
                monthly_spend = 0,
                budget_month = ?
            WHERE id = ?
            """,
            (
                current_month,
                row["id"],
            ),
        )


def get_api_key_identity(
    api_key: str,
) -> dict | None:

    if not api_key:
        return None

    key_hash = hash_api_key(api_key)

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                application_name,
                key_prefix,
                is_active,
                created_at,
                rate_limit,
                rate_window_seconds,
                allowed_models,
                monthly_budget,
                monthly_spend,
                budget_month
            FROM api_keys
            WHERE key_hash = ?
            """,
            (key_hash,),
        ).fetchone()

        if row is None:
            return None

        if not row["is_active"]:
            return None

        _reset_monthly_budget_if_needed(
            connection,
            row,
        )

        connection.commit()

        current_spend = row["monthly_spend"]

        if row["budget_month"] != current_budget_month():
            current_spend = 0

        return {
            "id": row["id"],
            "name": row["name"],
            "application_name": row[
                "application_name"
            ],
            "key_prefix": row[
                "key_prefix"
            ],
            "created_at": row[
                "created_at"
            ],
            "rate_limit": row[
                "rate_limit"
            ],
            "rate_window_seconds": row[
                "rate_window_seconds"
            ],
            "allowed_models": _parse_allowed_models(
                row["allowed_models"]
            ),
            "monthly_budget": float(
                row["monthly_budget"]
            ),
            "monthly_spend": float(
                current_spend
            ),
        }

    finally:
        connection.close()


def is_model_allowed(
    identity: dict,
    model: str,
) -> bool:

    allowed_models = identity.get(
        "allowed_models",
        ["*"],
    )

    if "*" in allowed_models:
        return True

    return model in allowed_models


def has_budget_available(
    identity: dict,
    estimated_cost: float = 0,
) -> bool:

    monthly_budget = float(
        identity.get(
            "monthly_budget",
            0,
        )
    )

    monthly_spend = float(
        identity.get(
            "monthly_spend",
            0,
        )
    )

    # 0 means unlimited.
    if monthly_budget <= 0:
        return True

    return (
        monthly_spend + estimated_cost
        <= monthly_budget
    )


def consume_budget(
    key_id: int,
    cost: float,
) -> bool:
    """
    Atomically consume monthly budget.

    Returns:
        True  -> cost was admitted and recorded.
        False -> request would exceed the monthly budget.

    A zero/negative budget means unlimited, matching the existing
    budget semantics.
    """

    if cost <= 0:
        return True

    connection = get_connection()

    try:
        # Serialize budget writers so concurrent requests cannot
        # both observe the same available balance.
        connection.execute(
            "BEGIN IMMEDIATE"
        )

        row = connection.execute(
            """
            SELECT
                id,
                is_active,
                monthly_budget,
                monthly_spend,
                budget_month
            FROM api_keys
            WHERE id = ?
            """,
            (key_id,),
        ).fetchone()

        if row is None:
            connection.rollback()
            return False

        if not row["is_active"]:
            connection.rollback()
            return False

        current_month = current_budget_month()

        monthly_budget = float(
            row["monthly_budget"]
        )

        monthly_spend = float(
            row["monthly_spend"]
        )

        # Reset spend when a new month starts.
        if row["budget_month"] != current_month:

            monthly_spend = 0.0

            connection.execute(
                """
                UPDATE api_keys
                SET
                    monthly_spend = 0,
                    budget_month = ?
                WHERE id = ?
                """,
                (
                    current_month,
                    key_id,
                ),
            )

        # 0 means unlimited.
        if monthly_budget > 0:

            if (
                monthly_spend + cost
                > monthly_budget
            ):
                connection.rollback()
                return False

        # Record the spend.
        connection.execute(
            """
            UPDATE api_keys
            SET
                monthly_spend = ?,
                budget_month = ?
            WHERE id = ?
            """,
            (
                monthly_spend + cost,
                current_month,
                key_id,
            ),
        )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_monthly_spend(
    key_id: int,
    cost: float,
) -> None:
    """
    Legacy/unconditional spend update.

    Kept for compatibility with existing code/tests.

    New request handling should use consume_budget() instead,
    because consume_budget enforces the budget atomically.
    """

    if cost <= 0:
        return

    connection = get_connection()

    try:

        current_month = current_budget_month()

        connection.execute(
            """
            UPDATE api_keys
            SET
                monthly_spend =
                    CASE
                        WHEN budget_month = ?
                        THEN monthly_spend + ?
                        ELSE ?
                    END,
                budget_month = ?
            WHERE id = ?
            """,
            (
                current_month,
                cost,
                cost,
                current_month,
                key_id,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def list_api_keys() -> list[dict]:

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                name,
                application_name,
                key_prefix,
                is_active,
                created_at,
                rate_limit,
                rate_window_seconds,
                allowed_models,
                monthly_budget,
                monthly_spend,
                budget_month
            FROM api_keys
            ORDER BY id DESC
            """
        ).fetchall()

        current_month = current_budget_month()

        result = []

        for row in rows:

            monthly_spend = row[
                "monthly_spend"
            ]

            if row["budget_month"] != current_month:
                monthly_spend = 0

            result.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "application_name": row[
                        "application_name"
                    ],
                    "key_prefix": row[
                        "key_prefix"
                    ],
                    "is_active": bool(
                        row["is_active"]
                    ),
                    "created_at": row[
                        "created_at"
                    ],
                    "rate_limit": row[
                        "rate_limit"
                    ],
                    "rate_window_seconds": row[
                        "rate_window_seconds"
                    ],
                    "allowed_models": _parse_allowed_models(
                        row["allowed_models"]
                    ),
                    "monthly_budget": float(
                        row["monthly_budget"]
                    ),
                    "monthly_spend": float(
                        monthly_spend
                    ),
                }
            )

        return result

    finally:
        connection.close()


def revoke_api_key(
    key_id: int,
) -> bool:

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            UPDATE api_keys
            SET is_active = 0
            WHERE id = ?
            """,
            (key_id,),
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()