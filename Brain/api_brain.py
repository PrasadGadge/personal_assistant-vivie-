# ==========================================
# Brain/api_brain.py — Streaming Response
# Yields sentences as they arrive from the API
# so TTS can start speaking before generation ends
# ==========================================

import os
import re
from openai import OpenAI

client = OpenAI(
    api_key  = os.getenv("OPENROUTER_API_KEY"),
    base_url = "https://openrouter.ai/api/v1"
)

MODEL       = "deepseek/deepseek-chat"
TEMPERATURE = 0.5
MAX_TOKENS  = 500

# Sentence boundary pattern
_SENT_END = re.compile(r'(?<=[.!?])\s+')


# ─────────────────────────────────────────────────
# STREAMING GENERATOR
# Yields complete sentences as they arrive
# ─────────────────────────────────────────────────

def stream_response(text: str):
    """
    Generator — yields one complete sentence at a time
    as the LLM streams tokens.

    Usage:
        for sentence in stream_response(prompt):
            speak_blocking(sentence)

    First sentence arrives in ~0.3-0.8s instead of
    waiting 2-3s for the full response.
    """
    buffer = ""

    try:
        stream = client.chat.completions.create(
            model    = MODEL,
            messages = [{"role": "user", "content": text}],
            temperature = TEMPERATURE,
            max_tokens  = MAX_TOKENS,
            stream      = True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta is None:
                continue

            buffer += delta

            # Yield complete sentences as they form
            while True:
                # Find next sentence boundary
                match = _SENT_END.search(buffer)
                if not match:
                    break

                sentence = buffer[:match.start() + 1].strip()
                buffer   = buffer[match.end():]

                if sentence:
                    yield sentence

        # Yield anything remaining
        remaining = buffer.strip()
        if remaining and len(remaining) > 2:
            yield remaining

    except Exception as e:
        print(f"[API Stream Error]: {e}")
        yield "I ran into an issue connecting. Please try again."


# ─────────────────────────────────────────────────
# BLOCKING FALLBACK
# Used by cl_brain.py for history/memory operations
# that need the full response before proceeding
# ─────────────────────────────────────────────────

def api_generate_response(text: str) -> str:
    """
    Blocking call — returns full response as string.
    Used when the full text is needed before action
    (e.g. memory extraction, reminder parsing, planning).
    """
    try:
        sentences = list(stream_response(text))
        return " ".join(sentences).strip()
    except Exception as e:
        print(f"[API Error]: {e}")
        return "I am unable to access advanced reasoning at the moment."
