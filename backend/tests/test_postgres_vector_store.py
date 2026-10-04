import pytest


psycopg = pytest.importorskip(
    "psycopg",
    reason="psycopg is not installed",
)

from app.core.config import settings
from app.cache.postgres_vector_store import (
    embedding_to_vector,
    PostgresVectorStore,
)


def postgres_vector_available() -> bool:

    try:

        with psycopg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        ) as connection:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_extension
                        WHERE extname = 'vector'
                    )
                    """
                )

                row = cursor.fetchone()

                return bool(row and row[0])

    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not postgres_vector_available(),
    reason=(
        "PostgreSQL/pgvector is not available"
    ),
)


def test_embedding_to_vector():

    embedding = [
        0.1,
        0.2,
        0.3,
    ]

    vector = embedding_to_vector(
        embedding
    )

    assert vector == "[0.1,0.2,0.3]"