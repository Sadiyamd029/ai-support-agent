import os

os.environ.pop("ANTHROPIC_API_KEY", None)  # force mock mode for tests
os.environ.pop("WEBHOOK_SECRET", None)

from fastapi.testclient import TestClient

from app.main import SESSIONS, app

client = TestClient(app)


def setup_function():
    SESSIONS.clear()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_chat_remembers_turns():
    client.post("/chat", json={"session_id": "s1", "message": "Hi"})
    r = client.post("/chat", json={"session_id": "s1", "message": "Where is my order?"})
    assert r.status_code == 200
    assert r.json()["turns"] == 2
    assert "reply" in r.json()


def test_chat_validation():
    r = client.post("/chat", json={"session_id": "s1", "message": ""})
    assert r.status_code == 422


def test_voice_webhook():
    r = client.post("/webhook/voice", json={"call_id": "42", "transcript": "I want to return a shirt"})
    assert r.status_code == 200
    assert r.json()["call_id"] == "42" and r.json()["speak"]


def test_webhook_secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "abc")
    r = client.post("/webhook/voice", json={"call_id": "1", "transcript": "hello"})
    assert r.status_code == 401
    r = client.post(
        "/webhook/voice",
        json={"call_id": "1", "transcript": "hello"},
        headers={"X-Webhook-Secret": "abc"},
    )
    assert r.status_code == 200


def test_reset():
    client.post("/chat", json={"session_id": "s2", "message": "Hi"})
    assert client.delete("/chat/s2").json()["cleared"] is True
    assert "s2" not in SESSIONS
