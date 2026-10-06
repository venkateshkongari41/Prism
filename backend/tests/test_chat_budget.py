import pytest
from fastapi.testclient import TestClient

from app.auth import service
from app.auth.dependencies import require_api_key
from app.core import config
from app.core.router import RoutingResult
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def create_budget_key(
    monthly_budget: float,
):
    api_key = service.create_api_key(
        name="chat-budget-test",
        application_name="chat-budget-app",
        monthly_budget=monthly_budget,
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    return api_key, identity


def test_chat_rejects_when_actual_cost_exceeds_budget(
    client,
    monkeypatch,
):

    api_key, identity = create_budget_key(
        monthly_budget=0.001
    )

    # Disable semantic cache for this endpoint test.
    monkeypatch.setattr(
        config.settings,
        "semantic_cache_enabled",
        False,
    )

    async def fake_rate_limit(identity):
        return 59

    async def fake_execute(
        alias,
        model,
        messages,
        stream=False,
    ):
        return RoutingResult(
            response={
                "id": "test-completion",
                "object": "chat.completion",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Test response",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "prism_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                    "cost": 0.002,
                },
            },
            provider="mock",
            fallback_used=False,
        )

    monkeypatch.setattr(
        "app.api.chat.check_rate_limit",
        fake_rate_limit,
    )

    monkeypatch.setattr(
        "app.api.chat.routing_engine.execute",
        fake_execute,
    )

    async def override_api_key():
        return identity

    app.dependency_overrides[
        require_api_key
    ] = override_api_key

    try:

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "fast",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
            },
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                )
            },
        )

        assert response.status_code == 402

        assert response.json() == {
            "detail": "Monthly budget exceeded"
        }

    finally:

        app.dependency_overrides.clear()


def test_chat_consumes_actual_cost_when_budget_allows(
    client,
    monkeypatch,
):

    api_key, identity = create_budget_key(
        monthly_budget=0.010
    )

    monkeypatch.setattr(
        config.settings,
        "semantic_cache_enabled",
        False,
    )

    async def fake_rate_limit(identity):
        return 59

    async def fake_execute(
        alias,
        model,
        messages,
        stream=False,
    ):
        return RoutingResult(
            response={
                "id": "test-completion",
                "object": "chat.completion",
                "model": "upstream/model-two",
                "choices": [],
                "prism_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "total_tokens": 20,
                    "cost": 0.002,
                },
            },
            provider="Provider Two",
            fallback_used=False,
            model="upstream/model-two",
        )

    monkeypatch.setattr(
        "app.api.chat.check_rate_limit",
        fake_rate_limit,
    )

    monkeypatch.setattr(
        "app.api.chat.routing_engine.execute",
        fake_execute,
    )

    app.dependency_overrides[
        require_api_key
    ] = lambda: identity

    try:

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "fast",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
            },
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                )
            },
        )

        assert response.status_code == 200

        assert (
            response.headers[
                "X-Prism-Cost-USD"
            ]
            == "0.0020000000"
        )

        refreshed_identity = (
            service.get_api_key_identity(
                api_key
            )
        )

        assert refreshed_identity is not None

        assert (
            refreshed_identity[
                "monthly_spend"
            ]
            == 0.002
        )

        from app.usage.usage_service import get_usage

        usage_record = get_usage(
            application_name=identity["application_name"],
            limit=1,
        )[0]
        assert usage_record["model"] == "upstream/model-two"
        assert usage_record["provider"] == "Provider Two"

    finally:

        app.dependency_overrides.clear()