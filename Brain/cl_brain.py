# ==========================================
# Brain/cl_brain.py — Streaming Brain
# Streams sentences to TTS as they arrive
# Cuts perceived latency from ~3s to ~0.5s
# ==========================================

import os
import re
import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    load_dotenv = None

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(BASE_DIR, "vivie_history.txt")
MAX_HISTORY_CHARS = 12000


# ─────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """You are Vivie, a private advanced AI system designed for a single user.

You are not a public chatbot. You are not a roleplay character.
You are a personal AI built for efficiency, intelligence, and clarity.

Personality:
- Calm, intelligent, observant
- Slightly witty when appropriate
- Confident but never arrogant
- Precise — never robotic, never overly emotional

Rules:
- Do NOT repeat the user's question
- Do NOT say "As an AI"
- Keep answers concise unless depth is requested
- Return only the final clear response
- Never generate fake tool usage

You are built for this specific user. Maintain steady presence."""


# ─────────────────────────────────────────────────
# INTENT DETECTION
# ─────────────────────────────────────────────────

def detect_intent(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["how old","age","when was","how many","what year"]):
        return "numeric"
    if any(w in t for w in ["who is","tell me about","biography"]):
        return "bio"
    if any(w in t for w in ["explain","why","how does","how do"]):
        return "deep"
    if any(w in t for w in ["current","live","real time","latest"]):
        return "realtime"
    if len(t.split()) <= 3:
        return "short"
    return "general"


# ─────────────────────────────────────────────────
# DYNAMIC PROMPT BUILDER
# ─────────────────────────────────────────────────

def build_system_prompt(intent: str) -> str:
    try:
        from Core_structure.personality_engine import get_personality_prompt
        personality_prompt = get_personality_prompt()
    except Exception:
        personality_prompt = ""

    prompt = BASE_SYSTEM_PROMPT
    if personality_prompt:
        prompt += f"\n\n{personality_prompt}"

    mode_map = {
        "numeric":  "\n\nResponse Mode: Answer in ONE short sentence only.",
        "short":    "\n\nResponse Mode: Keep answer under 2 lines.",
        "deep":     "\n\nResponse Mode: Provide structured explanation.",
        "realtime": "\n\nResponse Mode: If live data unavailable, state limitation confidently.",
    }
    prompt += mode_map.get(intent, "\n\nResponse Mode: Concise professional answer.")
    return prompt


# ─────────────────────────────────────────────────
# HISTORY HANDLING
# ─────────────────────────────────────────────────

def load_history() -> str:
    if not os.path.exists(HISTORY_FILE):
        return ""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def save_history(history: str):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(history)
    except Exception as e:
        print(f"[Brain] History save error: {e}")


def trim_history(history: str) -> str:
    if len(history) > MAX_HISTORY_CHARS:
        return history[-MAX_HISTORY_CHARS:]
    return history


def _extract_clean_user_text(full_prompt: str) -> str:
    """Extract just the user's question from the full LLM prompt."""
    match = re.search(r'\nUser:\s*(.+?)\n\nRespond now', full_prompt, re.DOTALL)
    if match:
        return match.group(1).strip()[:200]
    lines = full_prompt.strip().split('\n')
    for line in reversed(lines):
        if line.startswith('User:'):
            return line[5:].strip()[:200]
    return full_prompt[:200].strip()


# ─────────────────────────────────────────────────
# RESPONSE CLEANER
# ─────────────────────────────────────────────────

def clean_response(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"(AI:|Assistant:)", "", text, flags=re.IGNORECASE)
    return text.strip()


# ─────────────────────────────────────────────────
# STREAMING MAIN BRAIN
#
# Two modes:
#
# 1. Main_Brain(text) — blocking, returns full string
#    Used by: reminders, research agent, planning agent,
#    memory extraction, any flow that needs full response
#    before acting.
#
# 2. Main_Brain_Stream(text, on_sentence) — streaming
#    Calls on_sentence(sentence) for each sentence
#    as it arrives. Used by tts_loop for live speech.
#    Returns full response string when done.
# ─────────────────────────────────────────────────

def _build_full_prompt(text: str) -> tuple:
    """Build the full prompt and return (full_prompt, clean_user_text, intent)."""
    history  = load_history()
    ts       = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    intent   = detect_intent(text)
    sys_prompt = build_system_prompt(intent)

    clean_user = _extract_clean_user_text(text)
    history   += f"\n[{ts}] User: {clean_user}"
    history    = trim_history(history)

    full_prompt = sys_prompt + "\n\n" + history + "\n\n" + text
    return full_prompt, clean_user, intent, history, ts


def Main_Brain(text: str) -> str:
    """
    Blocking LLM call — returns complete response string.
    Use for: memory ops, agents, planning, reminder parsing.
    """
    try:
        from Brain.api_brain import api_generate_response
        full_prompt, clean_user, intent, history, ts = _build_full_prompt(text)

        response = api_generate_response(full_prompt)
        response = clean_response(response)

        if not response:
            return "I couldn't generate a response. Please try again."

        history += f"\n[{ts}] Vivie: {response[:300]}"
        history  = trim_history(history)
        save_history(history)

        return response

    except Exception as e:
        print(f"[Brain Error]: {e}")
        return "Processing interruption detected."


def Main_Brain_Stream(text: str, on_sentence=None) -> str:
    """
    Streaming LLM call.
    Calls on_sentence(sentence_str) for each sentence
    as it arrives from the API — before generation ends.

    Returns the complete response when done.
    Used by tts_loop for low-latency speech.

    Args:
        text:        Full context prompt
        on_sentence: Callback called with each sentence string.
                     If None, behaves like Main_Brain().
    """
    try:
        from Brain.api_brain import stream_response
        full_prompt, clean_user, intent, history, ts = _build_full_prompt(text)

        full_response = ""

        for sentence in stream_response(full_prompt):
            sentence = clean_response(sentence)
            if not sentence:
                continue

            full_response += sentence + " "

            # Fire callback immediately — TTS starts speaking
            if on_sentence:
                on_sentence(sentence.strip())

        full_response = full_response.strip()

        if not full_response:
            fallback = "I couldn't generate a response. Please try again."
            if on_sentence:
                on_sentence(fallback)
            return fallback

        # Save clean history
        history += f"\n[{ts}] Vivie: {full_response[:300]}"
        history  = trim_history(history)
        save_history(history)

        return full_response

    except Exception as e:
        print(f"[Brain Stream Error]: {e}")
        fallback = "Processing interruption detected."
        if on_sentence:
            on_sentence(fallback)
        return fallback
