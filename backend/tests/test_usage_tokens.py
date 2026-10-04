from app.usage.usage_service import (
    get_usage,
    record_usage,
)


def test_record_usage_with_tokens():

    usage_id = record_usage(
        application_id=1,
        application_name="token-test-app",
        model="fast",
        provider="openrouter",
        status="success",
        latency_ms=500.25,
        prompt_tokens=18,
        completion_tokens=420,
        total_tokens=438,
        cost=0.0,
    )

    assert usage_id is not None

    records = get_usage(
        application_name="token-test-app"
    )

    assert len(records) >= 1

    record = records[0]

    assert record["prompt_tokens"] == 18
    assert record["completion_tokens"] == 420
    assert record["total_tokens"] == 438
    assert record["cost"] == 0.0