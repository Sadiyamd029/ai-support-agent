# AI Support Agent API

A small FastAPI service that connects a customer-support chatbot ("Maya") to an LLM.
It exposes a **REST chat endpoint** for web/mobile apps and a **webhook endpoint**
that a voice-agent platform can call with a caller's transcribed speech.

## Features
- `POST /chat` – multi-turn chat with per-session memory
- `POST /webhook/voice` – voice-agent webhook, returns short speakable text; optional `X-Webhook-Secret` header check
- `DELETE /chat/{session_id}` – clear a conversation
- `GET /health` – status (`live` or `mock` mode)
- Simple web chat page at `/`
- Input validation (Pydantic), error handling (502 if the LLM fails), logging
- Runs offline in **mock mode** when no API key is set
- Unit tests with pytest; Postman collection included

## Tech
Python, FastAPI, Pydantic, Uvicorn, Anthropic API, pytest, Postman

## Run it
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add ANTHROPIC_API_KEY for live mode (optional)
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 for the chat page, or http://127.0.0.1:8000/docs for the interactive API docs.

## Example
```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"session_id":"user-123","message":"How do I return a shirt?"}'
```

## Test
```bash
pytest -q
```
Import `postman_collection.json` into Postman to try every endpoint.

## Project layout
```
app/main.py      API routes, sessions, webhook
app/llm.py       LLM wrapper + system prompt (mock fallback)
app/static/      minimal chat UI
tests/           pytest tests
```

## Possible next steps
Database for sessions, speech-to-text/text-to-speech integration, Docker, deployment.
