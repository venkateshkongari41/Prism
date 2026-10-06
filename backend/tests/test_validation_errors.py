from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_chat_request_returns_validation_error():

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "",
            "messages": [],
            "stream": False,
        },
        headers={
            "Authorization": "Bearer prism_live_F9RJk9g021hvyau4NyelMuyGES8n0RPTBrpUd1OFlic"
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "error" in body
    assert body["error"]["type"] == "validation_error"
    assert body["error"]["message"] == "Invalid request"
    assert "details" in body["error"]