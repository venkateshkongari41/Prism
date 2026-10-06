from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_request_id_is_generated():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id is not None
    assert len(request_id) > 0


def test_request_id_is_preserved():

    request_id = (
        "prism-test-request-123"
    )

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id
        },
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "X-Request-ID"
        ]
        == request_id
    )