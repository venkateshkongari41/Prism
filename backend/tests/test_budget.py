from datetime import datetime, timezone

from app.auth import service


def _create_test_key(
    monthly_budget: float,
) -> tuple[int, str]:
    api_key = service.create_api_key(
        name="budget-test",
        application_name="budget-test-app",
        monthly_budget=monthly_budget,
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    return identity["id"], api_key


def test_consume_budget_within_limit():

    key_id, api_key = _create_test_key(
        monthly_budget=1.00
    )

    assert (
        service.consume_budget(
            key_id,
            0.40,
        )
        is True
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    assert identity["monthly_spend"] == 0.40

def test_consume_budget_exact_limit():

    key_id, api_key = _create_test_key(
        monthly_budget=1.00
    )

    assert (
        service.consume_budget(
            key_id,
            1.00,
        )
        is True
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    assert identity["monthly_spend"] == 1.00


def test_consume_budget_rejects_over_limit():

    key_id, api_key = _create_test_key(
        monthly_budget=1.00
    )

    assert (
        service.consume_budget(
            key_id,
            0.75,
        )
        is True
    )

    assert (
        service.consume_budget(
            key_id,
            0.30,
        )
        is False
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    # Failed request must not change spend.
    assert identity["monthly_spend"] == 0.75


def test_zero_budget_is_unlimited():

    key_id, api_key = _create_test_key(
        monthly_budget=0
    )

    assert (
        service.consume_budget(
            key_id,
            100.00,
        )
        is True
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    assert identity["monthly_spend"] == 100.00


def test_zero_cost_is_ignored():

    key_id, api_key = _create_test_key(
        monthly_budget=1.00
    )

    assert (
        service.consume_budget(
            key_id,
            0,
        )
        is True
    )

    identity = service.get_api_key_identity(
        api_key
    )

    assert identity is not None

    assert identity["monthly_spend"] == 0