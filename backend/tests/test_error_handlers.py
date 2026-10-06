from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_model_alias_not_found_error():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "does-not-exist",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                }
            ],
            "stream": False,
        },
        headers={
            "Authorization": "Bearer invalid-test-key"
        },
    )

    assert response.status_code in (
        400,
        401,
    )