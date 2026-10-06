import uuid

from fastapi.testclient import TestClient

from app.auth import service
from app.auth.dependencies import require_api_key
from app.core.config import settings
from app.main import app


def create_test_identity():

    api_key = service.create_api_key(
        name="usage-api-test",
        application_name="usage-api-tenant",
        monthly_budget=10.0,
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    return api_key, identity


def test_usage_endpoint_is_tenant_scoped(
    monkeypatch,
):

    api_key, identity = create_test_identity()

    app.dependency_overrides[
        require_api_key
    ] = lambda: identity

    try:

        from app.usage.usage_service import (
            record_usage,
        )

        record_usage(
            application_id=identity["id"],
            application_name=(
                identity[
                    "application_name"
                ]
            ),
            model="fast",
            provider="mock",
            status="success",
            latency_ms=10.0,
            prompt_tokens=10,
            completion_tokens=10,
            total_tokens=20,
            cost=0.001,
            request_id="usage-api-test-001",
            cache_type="miss",
            fallback_used=False,
        )

        client = TestClient(app)

        response = client.get(
            "/v1/usage",
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                )
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert (
            body["application"]
            == "usage-api-tenant"
        )

        assert len(
            body["items"]
        ) >= 1

        latest = body["items"][0]

        assert (
            latest["application_name"]
            == "usage-api-tenant"
        )

    finally:

        app.dependency_overrides.clear()


def test_usage_summary_endpoint():

    api_key, identity = create_test_identity()

    app.dependency_overrides[
        require_api_key
    ] = lambda: identity

    try:

        from app.usage.usage_service import (
            record_usage,
        )

        record_usage(
            application_id=identity["id"],
            application_name=(
                identity[
                    "application_name"
                ]
            ),
            model="fast",
            provider="mock",
            status="success",
            latency_ms=25.0,
            prompt_tokens=20,
            completion_tokens=30,
            total_tokens=50,
            cost=0.002,
            request_id="usage-summary-test-001",
            cache_type="miss",
            fallback_used=False,
        )

        client = TestClient(app)

        response = client.get(
            "/v1/usage/summary",
            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                )
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert (
            body["application"]
            == "usage-api-tenant"
        )

        assert "summary" in body

        summary = body["summary"]

        assert summary[
            "total_requests"
        ] >= 1

        assert summary[
            "total_tokens"
        ] >= 50

        assert summary[
            "total_cost"
        ] >= 0.002

    finally:

        app.dependency_overrides.clear()


def test_admin_usage_summary_includes_model_provider_breakdown(
    monkeypatch,
):
    from app.usage.usage_service import record_usage

    application_name = f"admin-usage-{uuid.uuid4()}"
    monkeypatch.setattr(
        settings,
        "prism_admin_key",
        "test-admin-key",
    )

    record_usage(
        application_id=None,
        application_name=application_name,
        model="model-one",
        provider="provider-one",
        status="success",
        latency_ms=10.0,
    )
    record_usage(
        application_id=None,
        application_name=application_name,
        model="model-two",
        provider="provider-two",
        status="success",
        latency_ms=20.0,
    )

    response = TestClient(app).get(
        "/admin/usage/summary",
        params={"application_name": application_name},
        headers={"X-Prism-Admin-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["summary"]["model_provider_breakdown"] == [
        {
            "model": "model-one",
            "provider": "provider-one",
            "total_requests": 1,
            "successful_requests": 1,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        },
        {
            "model": "model-two",
            "provider": "provider-two",
            "total_requests": 1,
            "successful_requests": 1,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        },
    ]