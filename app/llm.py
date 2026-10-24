"""LLM wrapper. Uses the Anthropic API if a key is set, otherwise a simple mock
so the whole project can be run and tested offline."""
import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-5-5")

SYSTEM_PROMPT = (
    "You are Maya, a friendly customer-support assistant for a small online store. "
    "Help with order status, returns and general questions. Be concise and polite. "
    "If you do not know something, say so and offer to connect a human agent. "
    "Never invent order details."
)

VOICE_RULES = (
    " This reply will be spoken aloud on a phone call: use at most two short "
    "sentences, plain words, no lists, no emojis, no markdown."
)


def _client():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    from anthropic import Anthropic

    return Anthropic(api_key=key)


def generate_reply(history: list[dict], voice: bool = False) -> str:
    """history = [{"role": "user"|"assistant", "content": "..."}, ...]"""
    client = _client()
    system = SYSTEM_PROMPT + (VOICE_RULES if voice else "")
    if client is None:  # MOCK mode
        last = history[-1]["content"]
        return f"[mock reply] You said: '{last}'. I'm running without an API key."
    resp = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=system,
        messages=history,
    )
    return resp.content[0].text.strip()
