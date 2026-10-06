from uuid import uuid4

import pytest

from app.usage.usage_service import get_usage_summary, record_usage


def test_cache_hit_statistics():
    # Use a unique tenant/application name so repeated pytest runs
    # cannot pick up rows left behind by an earlier run.
    application_name = f"cache-stats-test-{uuid4().hex}"

    record_usage(
        application_id=9101,
        application_name=application_name,
        model="fast",
        provider="cache",
        status="success",
        latency_ms=2,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        cost=0,
        request_id="cache-exact-001",
        cache_type="exact",
        fallback_used=False,
    )

    record_usage(
        application_id=9101,
        application_name=application_name,
        model="fast",
        provider="cache",
        status="success",
        latency_ms=3,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        cost=0,
        request_id="cache-semantic-001",
        cache_type="semantic",
        fallback_used=False,
    )

    record_usage(
        application_id=9101,
        application_name=application_name,
        model="fast",
        provider="mock",
        status="success",
        latency_ms=100,
        prompt_tokens=10,
        completion_tokens=10,
        total_tokens=20,
        cost=0.001,
        request_id="cache-miss-001",
        cache_type="miss",
        fallback_used=True,
    )

    summary = get_usage_summary(
        application_name=application_name
    )

    assert summary["cache_hits"] == 2
    assert summary["cache_misses"] == 1
    assert summary["cache_hit_rate"] == pytest.approx(2 / 3)
    assert summary["fallback_requests"] == 1
