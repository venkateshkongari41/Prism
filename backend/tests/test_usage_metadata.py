from app.usage.usage_service import (
    get_usage,
    record_usage,
)


def test_usage_records_cache_metadata():

    record_id = record_usage(
        application_id=9001,
        application_name="tenant-a",
        model="fast",
        provider="cache",
        status="success",
        latency_ms=2.5,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        cost=0.0,
        request_id="req-cache-001",
        cache_type="semantic",
        fallback_used=False,
    )

    assert record_id is not None

    rows = get_usage(
        application_name="tenant-a",
        limit=1,
    )

    assert len(rows) == 1

    row = rows[0]

    assert row["provider"] == "cache"
    assert row["cache_type"] == "semantic"
    assert row["fallback_used"] is False
    assert row["request_id"] == "req-cache-001"


def test_usage_records_fallback():

    record_id = record_usage(
        application_id=9002,
        application_name="tenant-b",
        model="smart",
        provider="huggingface",
        status="success",
        latency_ms=125.0,
        prompt_tokens=20,
        completion_tokens=30,
        total_tokens=50,
        cost=0.003,
        request_id="req-fallback-001",
        cache_type="miss",
        fallback_used=True,
    )

    assert record_id is not None

    rows = get_usage(
        application_name="tenant-b",
        limit=1,
    )

    assert len(rows) == 1

    row = rows[0]

    assert row["cache_type"] == "miss"
    assert row["fallback_used"] is True
    assert row["provider"] == "huggingface"
    assert row["total_tokens"] == 50
    assert row["cost"] == 0.003