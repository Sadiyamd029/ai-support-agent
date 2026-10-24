"""AI Support Agent API
REST + webhook service that lets a chat UI or a voice platform talk to an LLM."""
import logging
import os
from collections import defaultdict

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.llm import generate_reply

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("support-agent")

app = FastAPI(title="AI Support Agent API", version="1.0.0")

# In-memory conversation store: session_id -> list of messages (resets on restart)
SESSIONS: dict[str, list[dict]] = defaultdict(list)
MAX_TURNS = 10  # keep only the last N messages to limit cost/context


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, examples=["user-123"])
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    turns: int


class VoiceWebhook(BaseModel):
    call_id: str
    transcript: str = Field(..., min_length=1, max_length=2000)


def _converse(session_id: str, text: str, voice: bool = False) -> str:
    history = SESSIONS[session_id]
    history.append({"role": "user", "content": text})
    try:
        reply = generate_reply(history[-MAX_TURNS:], voice=voice)
    except Exception as exc:  # network error, bad key, rate limit...
        history.pop()  # don't keep a message that got no answer
        log.error("LLM call failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM service unavailable")
    history.append({"role": "assistant", "content": reply})
    return reply


@app.get("/health")
def health():
    return {"status": "ok", "mode": "live" if os.getenv("ANTHROPIC_API_KEY") else "mock"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = _converse(req.session_id, req.message)
    return ChatResponse(
        session_id=req.session_id, reply=reply, turns=len(SESSIONS[req.session_id]) // 2
    )


@app.post("/webhook/voice")
def voice_webhook(body: VoiceWebhook, x_webhook_secret: str | None = Header(default=None)):
    """Called by a voice platform with the caller's transcribed speech.
    Returns short text that the platform converts back to speech."""
    expected = os.getenv("WEBHOOK_SECRET")
    if expected and x_webhook_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    reply = _converse(f"call-{body.call_id}", body.transcript, voice=True)
    return {"call_id": body.call_id, "speak": reply}


@app.delete("/chat/{session_id}")
def reset(session_id: str):
    SESSIONS.pop(session_id, None)
    return {"session_id": session_id, "cleared": True}


@app.get("/")
def home():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
