import uuid
from datetime import datetime, timedelta, timezone

from app.auth.database import get_connection
from app.usage.usage_service import (
    get_usage,
    get_usage_by_application,
    get_usage_summary,
    record_usage,
)


def test_record_and_get_usage():

    usage_id = record_usage(
        application_id=1,
        application_name="test-app",
        model="test-model",
        provider="test-provider",
        status="success",
        latency_ms=125.5,
    )

    assert usage_id is not None

    records = get_usage(
        application_name="test-app"
    )

    assert len(records) >= 1

    record = records[0]

    assert (
        record["application_name"]
        == "test-app"
    )

    assert (
        record["model"]
        == "test-model"
    )

    assert (
        record["provider"]
        == "test-provider"
    )

    assert (
        record["status"]
        == "success"
    )

    assert (
        record["latency_ms"]
        == 125.5
    )


def test_usage_summary():

    application_name = (
        f"summary-test-{uuid.uuid4()}"
    )

    record_usage(
        application_id=2,
        application_name=application_name,
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=100.0,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        cost=0.01,
    )

    record_usage(
        application_id=2,
        application_name=application_name,
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=200.0,
        prompt_tokens=20,
        completion_tokens=30,
        total_tokens=50,
        cost=0.02,
    )

    record_usage(
        application_id=2,
        application_name=application_name,
        model="fast",
        provider="openrouter",
        status="failed",
        latency_ms=300.0,
    )

    summary = get_usage_summary(
        application_name=application_name
    )

    assert summary["total_requests"] == 3
    assert summary["successful_requests"] == 2
    assert summary["failed_requests"] == 1

    assert summary["total_prompt_tokens"] == 30
    assert summary["total_completion_tokens"] == 50
    assert summary["total_tokens"] == 80

    assert (
        abs(summary["total_cost"] - 0.03)
        < 0.000001
    )

    assert (
        summary["average_latency_ms"]
        == 200.0
    )


def test_usage_summary_breaks_down_model_and_provider():
    application_name = (
        f"summary-breakdown-{uuid.uuid4()}"
    )

    record_usage(
        application_id=3,
        application_name=application_name,
        model="model-one",
        provider="provider-one",
        status="success",
        latency_ms=100.0,
        total_tokens=15,
        cost=0.01,
    )
    record_usage(
        application_id=3,
        application_name=application_name,
        model="model-two",
        provider="provider-two",
        status="failed",
        latency_ms=200.0,
        total_tokens=5,
        cost=0.002,
    )

    summary = get_usage_summary(
        application_name=application_name
    )

    assert summary["model_provider_breakdown"] == [
        {
            "model": "model-one",
            "provider": "provider-one",
            "total_requests": 1,
            "successful_requests": 1,
            "failed_requests": 0,
            "total_tokens": 15,
            "total_cost": 0.01,
        },
        {
            "model": "model-two",
            "provider": "provider-two",
            "total_requests": 1,
            "successful_requests": 0,
            "failed_requests": 1,
            "total_tokens": 5,
            "total_cost": 0.002,
        },
    ]


def test_usage_by_application():

    application_a = (
        f"app-a-{uuid.uuid4()}"
    )

    application_b = (
        f"app-b-{uuid.uuid4()}"
    )

    record_usage(
        application_id=10,
        application_name=application_a,
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=100.0,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        cost=0.01,
    )

    record_usage(
        application_id=10,
        application_name=application_a,
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=200.0,
        prompt_tokens=20,
        completion_tokens=30,
        total_tokens=50,
        cost=0.02,
    )

    record_usage(
        application_id=11,
        application_name=application_b,
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=300.0,
        prompt_tokens=5,
        completion_tokens=10,
        total_tokens=15,
        cost=0.005,
    )

    results = get_usage_by_application()

    app_a = next(
        item
        for item in results
        if item["application_name"]
        == application_a
    )

    assert app_a["total_requests"] == 2
    assert app_a["successful_requests"] == 2

    assert (
        app_a["total_prompt_tokens"]
        == 30
    )

    assert (
        app_a["total_completion_tokens"]
        == 50
    )

    assert (
        app_a["total_tokens"]
        == 80
    )

    assert (
        abs(app_a["total_cost"] - 0.03)
        < 0.000001
    )

    assert (
        app_a["average_latency_ms"]
        == 150.0
    )


def test_usage_summary_with_hours_filter():

    application_name = (
        f"hours-summary-{uuid.uuid4()}"
    )

    record_usage(
        application_id=20,
        application_name=application_name,
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=100.0,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        cost=0.01,
    )

    old_timestamp = (
        datetime.now(timezone.utc)
        - timedelta(hours=48)
    ).isoformat()

    connection = get_connection()

    try:
        connection.execute(
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
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                20,
                application_name,
                "fast",
                "openrouter",
                "success",
                200.0,
                20,
                30,
                50,
                0.02,
                old_timestamp,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    summary = get_usage_summary(
        application_name=application_name,
        hours=24,
    )

    assert summary["total_requests"] == 1
    assert summary["successful_requests"] == 1
    assert summary["total_tokens"] == 30


def test_usage_by_application_with_hours_filter():

    application_name = (
        f"hours-app-{uuid.uuid4()}"
    )

    record_usage(
        application_id=30,
        application_name=application_name,
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=100.0,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        cost=0.01,
    )

    old_timestamp = (
        datetime.now(timezone.utc)
        - timedelta(hours=48)
    ).isoformat()

    connection = get_connection()

    try:
        connection.execute(
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
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                30,
                application_name,
                "fast",
                "openrouter",
                "success",
                200.0,
                20,
                30,
                50,
                0.02,
                old_timestamp,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    results = get_usage_by_application(
        hours=24
    )

    application = next(
        item
        for item in results
        if item["application_name"]
        == application_name
    )

    assert (
        application["total_requests"]
        == 1
    )

    assert (
        application["total_tokens"]
        == 30
    )


def test_usage_summary_rejects_invalid_hours():

    try:
        get_usage_summary(hours=0)
        assert False
    except ValueError as exc:
        assert (
            str(exc)
            == "hours must be greater than 0"
        )


def test_usage_by_application_rejects_invalid_hours():

    try:
        get_usage_by_application(hours=-1)
        assert False
    except ValueError as exc:
        assert (
            str(exc)
            == "hours must be greater than 0"
        )