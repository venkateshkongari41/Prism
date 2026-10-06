import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.cache.embedding import create_embedding
from app.cache.text import messages_to_text
from app.core.config import settings


SEMANTIC_INDEX_PREFIX = "prism:semantic:index"


class SemanticCache:

    def __init__(self, redis_client):
        self.redis = redis_client

    def _index_key(self, application_id: int) -> str:
        return f"{SEMANTIC_INDEX_PREFIX}:{application_id}"

    def _key(
        self,
        application_id: int,
        model: str,
        messages: list[dict[str, Any]],
    ) -> str:
        prompt_text = messages_to_text(messages)

        raw = (
            f"{application_id}:"
            f"{model}:"
            f"{prompt_text}"
        )

        digest = hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

        return f"prism:semantic:{application_id}:{model}:{digest}"

    async def get(
        self,
        *,
        application_id: int,
        model: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        cache_key = self._key(
            application_id=application_id,
            model=model,
            messages=messages,
        )

        # ---------------------------------------------------------
        # 1. Exact cache lookup
        # ---------------------------------------------------------

        cached = await self.redis.get(cache_key)

        if cached:
            value = json.loads(cached)

            return {
                "response": value["response"],
                "similarity": 1.0,
                "cache_type": "exact",
            }

        # ---------------------------------------------------------
        # 2. Semantic cache lookup
        # ---------------------------------------------------------

        prompt_text = messages_to_text(messages)
        query_embedding = create_embedding(prompt_text)

        index_key = self._index_key(application_id)

        cache_keys = await self.redis.smembers(
            index_key
        )

        best_match = None
        best_similarity = 0.0

        for candidate_key in cache_keys:

            candidate_json = await self.redis.get(
                candidate_key
            )

            if not candidate_json:
                continue

            candidate = json.loads(candidate_json)

            # Defensive tenant check.
            if candidate["application_id"] != application_id:
                continue

            # Keep semantic cache model-specific.
            if candidate["model"] != model:
                continue

            candidate_embedding = candidate["embedding"]

            similarity = self._cosine_similarity(
                query_embedding,
                candidate_embedding,
            )

            if similarity > best_similarity:

                best_similarity = similarity

                best_match = candidate

                best_match["cache_key"] = candidate_key

        if (
            best_match is not None
            and best_similarity
            >= settings.semantic_cache_similarity_threshold
        ):
            return {
                "response": best_match["response"],
                "similarity": best_similarity,
                "cache_type": "semantic",
            }

        return None

    async def set(
        self,
        *,
        application_id: int,
        model: str,
        messages: list[dict[str, Any]],
        response: dict[str, Any],
    ) -> None:

        cache_key = self._key(
            application_id=application_id,
            model=model,
            messages=messages,
        )

        prompt_text = messages_to_text(messages)
        embedding = create_embedding(prompt_text)

        value = {
            "application_id": application_id,
            "model": model,
            "prompt_text": prompt_text,
            "embedding": embedding,
            "response": response,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        await self.redis.set(
            cache_key,
            json.dumps(value),
            ex=settings.semantic_cache_ttl,
        )

        # Tenant-specific semantic index.
        await self.redis.sadd(
            self._index_key(application_id),
            cache_key,
        )

    @staticmethod
    def _cosine_similarity(
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:

        if not vector_a or not vector_b:
            return 0.0

        dot_product = sum(
            a * b
            for a, b in zip(
                vector_a,
                vector_b,
            )
        )

        magnitude_a = sum(
            a * a
            for a in vector_a
        ) ** 0.5

        magnitude_b = sum(
            b * b
            for b in vector_b
        ) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (
            magnitude_a * magnitude_b
        )