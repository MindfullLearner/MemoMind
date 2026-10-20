
import pytest
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_chat_success(monkeypatch):
    def fake_generate_reply(conversation_id, message):
        return "This is a mocked AI response."

    monkeypatch.setattr(main, "generate_reply", fake_generate_reply)

    response = client.post(
        "/chat",
        json={"message": "Hello", "conversation_id": "test-conversation"},
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "test-conversation"
    assert response.json()["response"] == "This is a mocked AI response."


def test_chat_missing_message():
    response = client.post("/chat", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_chat_service_error(monkeypatch):
    def fake_generate_reply(conversation_id, message):
        raise RuntimeError("Simulated service failure")

    monkeypatch.setattr(main, "generate_reply", fake_generate_reply)

    response = client.post(
        "/chat",
        json={"message": "Hello"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "HTTP_ERROR"


def test_chat_stream(monkeypatch):
    def fake_stream_reply(conversation_id, message):
        yield "Hello"
        yield " world"

    monkeypatch.setattr(main, "stream_reply", fake_stream_reply)

    response = client.post(
        "/chat/stream",
        json={"message": "Hello"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: conversation" in response.text
    assert 'data: {"text": "Hello"}' in response.text
    assert 'data: {"text": " world"}' in response.text
    assert "event: done" in response.text


def test_chat_stream_error(monkeypatch):
    def fake_stream_reply(conversation_id, message):
        raise RuntimeError("Simulated streaming failure")
        yield "unreachable"

    monkeypatch.setattr(main, "stream_reply", fake_stream_reply)

    response = client.post(
        "/chat/stream",
        json={"message": "Hello"},
    )

    assert response.status_code == 200
    assert "event: error" in response.text
    assert '"code": "STREAM_ERROR"' in response.text
