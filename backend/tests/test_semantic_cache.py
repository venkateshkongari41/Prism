import pytest
from importlib import import_module

from app.cache.semantic_cache import SemanticCache


class FakeRedis:

    def __init__(self):
        self.data = {}
        self.set_members = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value

    async def sadd(self, key, value):
        self.set_members.setdefault(
            key,
            set(),
        ).add(value)

    async def smembers(self, key):
        return self.set_members.get(
            key,
            set(),
        )


@pytest.mark.asyncio
async def test_tenant_isolation(monkeypatch):

    def fake_embedding(text):

        text = text.lower()

        if (
            "capital city of india" in text
            or "india's capital" in text
        ):
            return [1.0, 0.0, 0.0]

        return [0.0, 1.0, 0.0]

    semantic_cache_module = import_module(
        "app.cache.semantic_cache"
    )

    monkeypatch.setattr(
        semantic_cache_module,
        "create_embedding",
        fake_embedding,
    )

    redis = FakeRedis()

    cache = SemanticCache(redis)

    original_messages = [
        {
            "role": "user",
            "content": "What is the capital city of India?",
        }
    ]

    paraphrased_messages = [
        {
            "role": "user",
            "content": "Tell me India's capital.",
        }
    ]

    response = {
        "id": "test-response",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "New Delhi",
                }
            }
        ],
    }

    # Tenant A stores response
    await cache.set(
        application_id=100,
        model="fast",
        messages=original_messages,
        response=response,
    )

    # Tenant A -> semantic HIT
    tenant_a_result = await cache.get(
        application_id=100,
        model="fast",
        messages=paraphrased_messages,
    )

    assert tenant_a_result is not None

    assert (
        tenant_a_result["cache_type"]
        == "semantic"
    )

    assert (
        tenant_a_result["response"]
        == response
    )

    # Tenant B -> MISS
    tenant_b_result = await cache.get(
        application_id=200,
        model="fast",
        messages=paraphrased_messages,
    )

    assert tenant_b_result is None