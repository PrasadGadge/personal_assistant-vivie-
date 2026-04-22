# ==================================================
# voice_personality.py — Vivie Voice Personality (FIXED)
# ==================================================

import re
import os
import json
import datetime

# 🛠 SETTING: If Vivie reads "Less than speak version...", set this to False!
USE_SSML = False

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_FILE = os.path.join(BASE_DIR, "data", "voice_profile.json")

VOICE = "en-US-AriaNeural"

VOICE_PROFILES = {
    "default":    {"voice": VOICE, "rate": "+0%",   "pitch": "+0Hz",  "volume": "+0%",  "style": "chat",       "styledegree": "1.0"},
    "casual":     {"voice": VOICE, "rate": "+8%",   "pitch": "+2Hz",  "volume": "+0%",  "style": "chat",       "styledegree": "1.2"},
    "technical":  {"voice": VOICE, "rate": "-8%",   "pitch": "-1Hz",  "volume": "+5%",  "style": "chat",       "styledegree": "0.8"},
    "excited":    {"voice": VOICE, "rate": "+12%",  "pitch": "+5Hz",  "volume": "+8%",  "style": "excited",    "styledegree": "1.5"},
    "serious":    {"voice": VOICE, "rate": "-12%",  "pitch": "-3Hz",  "volume": "+10%", "style": "empathetic", "styledegree": "1.2"},
    "greeting":   {"voice": VOICE, "rate": "+5%",   "pitch": "+3Hz",  "volume": "+5%",  "style": "friendly",   "styledegree": "1.3"},
    "suggestion": {"voice": VOICE, "rate": "+0%",   "pitch": "+1Hz",  "volume": "-5%",  "style": "chat",       "styledegree": "0.9"},
    "concerned":  {"voice": VOICE, "rate": "-5%",   "pitch": "-2Hz",  "volume": "+5%",  "style": "empathetic", "styledegree": "1.1"},
    "thinking":   {"voice": VOICE, "rate": "-5%",   "pitch": "-1Hz",  "volume": "+0%",  "style": "chat",       "styledegree": "0.85"},
}

_MOOD_KEYWORDS = {
    "greeting":   ["good morning", "good evening", "good afternoon", "welcome back", "hello boss", "hey boss", "good to see"],
    "excited":    ["amazing", "excellent", "perfect", "great news", "fantastic", "wonderful", "incredible", "successfully", "done!", "completed", "that works"],
    "serious":    ["warning", "alert", "critical", "error", "failed", "battery low", "danger", "urgent", "important", "unable to"],
    "technical":  ["algorithm", "function", "code", "python", "neural", "database", "api", "system", "framework", "implementation", "memory", "token", "model", "latency"],
    "suggestion": ["you might", "perhaps", "suggestion", "consider", "you usually", "based on your", "might want to", "i noticed"],
    "concerned":  ["trouble", "issue", "problem", "unfortunately", "unable", "failed", "sorry", "couldn't"],
}

def detect_voice_mood(text: str, intent: str = "chat") -> str:
    t = text.lower()
    for mood, keywords in _MOOD_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return mood
    if intent in ("automation", "file_creation"):
        return "casual"
    if intent in ("research", "chat") and len(text.split()) > 50:
        return "technical"
    return "default"

def _get_personality_adjustments() -> dict:
    try:
        from Core_structure.personality_engine import _load
        p = _load()
        rate_adj, pitch_adj = 0, 0
        tone, warmth, depth = p.get("tone", 0.5), p.get("warmth", 0.5), p.get("technical_depth", 0.5)
        if tone > 0.6: rate_adj += 5
        elif tone < 0.3: rate_adj -= 5
        if warmth > 0.6: pitch_adj += 1
        elif warmth < 0.3: pitch_adj -= 1
        if depth > 0.6: rate_adj -= 3
        return {"rate_adj": rate_adj, "pitch_adj": pitch_adj}
    except Exception:
        return {"rate_adj": 0, "pitch_adj": 0}

def get_time_based_adjustment() -> dict:
    hour = datetime.datetime.now().hour
    if 5 <= hour < 9: return {"rate_adj": -3, "volume_adj": -5}
    elif 9 <= hour < 17: return {"rate_adj": 0, "volume_adj": 0}
    elif 17 <= hour < 21: return {"rate_adj": -2, "volume_adj": -2}
    else: return {"rate_adj": -5, "volume_adj": -8}

def _parse_int(s: str) -> int:
    return int(s.replace("%", "").replace("Hz", "").replace("+", ""))

def _fmt_pct(v: int) -> str: return f"+{v}%" if v >= 0 else f"{v}%"
def _fmt_hz(v: int) -> str: return f"+{v}Hz" if v >= 0 else f"{v}Hz"

def get_voice_params(text: str, intent: str = "chat") -> dict:
    mood = detect_voice_mood(text, intent)
    profile = VOICE_PROFILES.get(mood, VOICE_PROFILES["default"])
    pers_adj = _get_personality_adjustments()
    time_adj = get_time_based_adjustment()

    try:
        rate_val = _parse_int(profile["rate"]) + pers_adj.get("rate_adj",0) + time_adj.get("rate_adj",0)
        pitch_val = _parse_int(profile["pitch"]) + pers_adj.get("pitch_adj",0)
        vol_val = _parse_int(profile["volume"]) + time_adj.get("volume_adj",0)
        return {
            "voice": profile["voice"], "rate": _fmt_pct(rate_val), "pitch": _fmt_hz(pitch_val),
            "volume": _fmt_pct(vol_val), "mood": mood, "style": profile.get("style", "chat"), "styledegree": profile.get("styledegree", "1.0"),
        }
    except Exception:
        return {"voice": profile["voice"], "rate": profile["rate"], "pitch": profile["pitch"], "volume": profile["volume"], "mood": mood, "style": profile.get("style", "chat"), "styledegree": profile.get("styledegree", "1.0")}

def build_ssml(text: str, intent: str = "chat") -> str:
    """Builds SSML or returns plain text based on USE_SSML toggle."""
    
    # 1. Clean Markdown immediately
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s', '', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = text.strip()

    if not USE_SSML:
        return text # Return clean text if SSML is disabled

    params = get_voice_params(text, intent)
    
    # Natural pauses
    text = re.sub(r'\bBoss,\s*', 'Boss, <break time="180ms"/> ', text)
    text = re.sub(r'([.!?])\s+([A-Z])', r'\1 <break time="280ms"/> \2', text)
    text = re.sub(r':\s+', ': <break time="150ms"/> ', text)
    text = re.sub(r'\s*—\s*', ' <break time="200ms"/> ', text)

    # Emphasis
    for word in ["warning", "critical", "urgent", "danger", "never", "always", "must"]:
        text = re.sub(rf'\b({re.escape(word)})\b', r'<emphasis level="strong">\1</emphasis>', text, flags=re.IGNORECASE)

    voice, rate, pitch, volume = params["voice"], params["rate"], params["pitch"], params["volume"]
    style, degree = params.get("style", "chat"), params.get("styledegree", "1.0")

    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">'
        f'<voice name="{voice}"><mstts:express-as style="{style}" styledegree="{degree}">'
        f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">{text}</prosody>'
        f'</mstts:express-as></voice></speak>'
    )
