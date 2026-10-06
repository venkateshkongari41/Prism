import json
from typing import Any

from app.db.postgres import (
    get_postgres_connection,
)


def _embedding_to_pgvector(
    embedding: list[float],
) -> str:

    return (
        "["
        + ",".join(
            str(float(value))
            for value in embedding
        )
        + "]"
    )


class PostgresVectorStore:

    def save(
        self,
        *,
        cache_key: str,
        model: str,
        prompt_text: str,
        response: dict[str, Any],
        embedding: list[float],
    ) -> None:

        vector_value = (
            _embedding_to_pgvector(
                embedding
            )
        )

        with get_postgres_connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO
                    semantic_cache_entries (
                        cache_key,
                        model,
                        prompt_text,
                        response_json,
                        embedding
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s::jsonb,
                        %s::vector
                    )
                    """,
                    (
                        cache_key,
                        model,
                        prompt_text,
                        json.dumps(response),
                        vector_value,
                    ),
                )

            connection.commit()


    def search(
        self,
        *,
        model: str,
        embedding: list[float],
        threshold: float = 0.90,
    ) -> dict[str, Any] | None:

        vector_value = (
            _embedding_to_pgvector(
                embedding
            )
        )

        with get_postgres_connection() as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
                        cache_key,
                        prompt_text,
                        response_json,
                        1 - (
                            embedding <=> %s::vector
                        ) AS similarity
                    FROM semantic_cache_entries
                    WHERE model = %s
                    ORDER BY
                        embedding <=> %s::vector
                    LIMIT 1
                    """,
                    (
                        vector_value,
                        model,
                        vector_value,
                    ),
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                similarity = float(
                    row[5]
                )

                if similarity < threshold:
                    return None

                cursor.execute(
                    """
                    UPDATE semantic_cache_entries
                    SET hit_count = hit_count + 1
                    WHERE id = %s
                    """,
                    (row[0],),
                )

                connection.commit()

                return {
                    "id": row[0],
                    "cache_key": row[1],
                    "prompt_text": row[2],
                    "response": row[3],
                    "similarity": similarity,
                    "cache_type": "semantic",
                }