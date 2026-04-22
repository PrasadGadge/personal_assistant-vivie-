# ==================================================
# personality_engine.py — Vivie Evolving Personality
# The personality that becomes uniquely yours over time
# ==================================================

import json
import os
import datetime

BASE_DIR          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONALITY_FILE  = os.path.join(BASE_DIR, "data", "personality.json")

# ─────────────────────────────────────────────────
# DEFAULT PERSONALITY — neutral starting point
# All dimensions on a 0.0 → 1.0 scale
# ─────────────────────────────────────────────────

DEFAULT_PERSONALITY = {

    # How long responses are
    # 0.0 = very short  |  1.0 = very detailed
    "response_length": 0.5,

    # How formal or casual
    # 0.0 = very formal  |  1.0 = very casual/witty
    "tone": 0.4,

    # How often Vivie speaks without being asked
    # 0.0 = only when asked  |  1.0 = very proactive
    "proactivity": 0.5,

    # Technical depth of answers
    # 0.0 = simple explanations  |  1.0 = deep technical
    "technical_depth": 0.5,

    # Warmth of personality
    # 0.0 = professional/cold  |  1.0 = warm/personal
    "warmth": 0.4,

    # ── Tracking data ─────────────────────────────
    "total_interactions":    0,
    "positive_reactions":    0,
    "negative_reactions":    0,
    "last_updated":          "",
    "evolution_log":         [],  # history of changes
    "user_signals":          {}   # raw signals collected
}


# ─────────────────────────────────────────────────
# LOAD / SAVE
# ─────────────────────────────────────────────────

def _load() -> dict:
    if not os.path.exists(PERSONALITY_FILE):
        _save(DEFAULT_PERSONALITY.copy())
        return DEFAULT_PERSONALITY.copy()
    try:
        with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for key, val in DEFAULT_PERSONALITY.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception:
        return DEFAULT_PERSONALITY.copy()


def _save(data: dict):
    try:
        os.makedirs(os.path.dirname(PERSONALITY_FILE), exist_ok=True)
        with open(PERSONALITY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[PersonalityEngine] Save error: {e}")


# ─────────────────────────────────────────────────
# SIGNAL DETECTOR
# Reads signals from user behavior
# ─────────────────────────────────────────────────

def detect_signals(
    user_input:     str,
    vivie_response: str,
    intent:         str,
    reaction:       str = "neutral"
) -> dict:
    """
    Detect personality signals from a single interaction.
    Returns dict of signals found.
    """
    signals = {}
    text    = user_input.lower().strip()
    resp    = vivie_response.lower().strip()

    # ── Response length signals ───────────────────
    if any(w in text for w in ["too long", "shorter", "brief", "quick", "tldr", "summarize"]):
        signals["wants_shorter"]  = True

    if any(w in text for w in ["more detail", "explain more", "elaborate", "deeper", "full explanation"]):
        signals["wants_longer"]   = True

    if len(vivie_response.split()) < 20 and reaction == "positive":
        signals["liked_short"]    = True

    if len(vivie_response.split()) > 80 and reaction == "positive":
        signals["liked_long"]     = True

    # ── Tone signals ──────────────────────────────
    if any(w in text for w in ["be casual", "relax", "chill", "talk normally", "be funny"]):
        signals["wants_casual"]   = True

    if any(w in text for w in ["be professional", "formal", "serious", "no jokes"]):
        signals["wants_formal"]   = True

    if any(w in text for w in ["haha", "lol", "funny", "good joke", "witty"]):
        signals["liked_humor"]    = True

    # ── Technical depth signals ───────────────────
    technical_intents = ["file_creation", "automation", "code", "research"]
    if intent in technical_intents:
        signals["technical_user"] = True

    if any(w in text for w in ["too technical", "simpler", "easier", "i don't understand"]):
        signals["wants_simpler"]  = True

    if any(w in text for w in ["more technical", "deep dive", "advanced", "in detail"]):
        signals["wants_deeper"]   = True

    # ── Proactivity signals ───────────────────────
    if any(w in text for w in ["stop suggesting", "don't interrupt", "too proactive", "quiet"]):
        signals["wants_less_proactive"] = True

    if any(w in text for w in ["good suggestion", "nice idea", "proactive", "that was helpful"]):
        signals["liked_proactive"]      = True

    # ── Warmth signals ────────────────────────────
    if any(w in text for w in ["be more friendly", "warmer", "personal", "feel cold", "robotic"]):
        signals["wants_warmer"]   = True

    if any(w in text for w in ["professional", "just answer", "no small talk"]):
        signals["wants_colder"]   = True

    if reaction == "positive":
        signals["general_positive"] = True
    if reaction == "negative":
        signals["general_negative"] = True

    return signals


# ─────────────────────────────────────────────────
# EVOLVE PERSONALITY
# Updates personality based on signals
# ─────────────────────────────────────────────────

def evolve_personality(signals: dict):
    """
    Update personality dimensions based on detected signals.
    Each signal nudges the value slightly — gradual evolution.
    """
    if not signals:
        return

    p    = _load()
    step = 0.03  # small nudge per signal — gradual change

    changed = []

    # ── Response Length ───────────────────────────
    if signals.get("wants_shorter") or signals.get("liked_short"):
        if p["response_length"] > 0.1:
            p["response_length"] = round(p["response_length"] - step, 3)
            changed.append(f"response_length ↓ {p['response_length']:.2f}")

    if signals.get("wants_longer") or signals.get("liked_long"):
        if p["response_length"] < 0.9:
            p["response_length"] = round(p["response_length"] + step, 3)
            changed.append(f"response_length ↑ {p['response_length']:.2f}")

    # ── Tone ──────────────────────────────────────
    if signals.get("wants_casual") or signals.get("liked_humor"):
        if p["tone"] < 0.9:
            p["tone"] = round(p["tone"] + step, 3)
            changed.append(f"tone ↑ {p['tone']:.2f}")

    if signals.get("wants_formal"):
        if p["tone"] > 0.1:
            p["tone"] = round(p["tone"] - step, 3)
            changed.append(f"tone ↓ {p['tone']:.2f}")

    # ── Technical Depth ───────────────────────────
    if signals.get("technical_user") or signals.get("wants_deeper"):
        if p["technical_depth"] < 0.9:
            p["technical_depth"] = round(p["technical_depth"] + step, 3)
            changed.append(f"technical_depth ↑ {p['technical_depth']:.2f}")

    if signals.get("wants_simpler"):
        if p["technical_depth"] > 0.1:
            p["technical_depth"] = round(p["technical_depth"] - step, 3)
            changed.append(f"technical_depth ↓ {p['technical_depth']:.2f}")

    # ── Proactivity ───────────────────────────────
    if signals.get("likes_proactive"):
        if p["proactivity"] < 0.9:
            p["proactivity"] = round(p["proactivity"] + step, 3)
            changed.append(f"proactivity ↑ {p['proactivity']:.2f}")

    if signals.get("wants_less_proactive"):
        if p["proactivity"] > 0.1:
            p["proactivity"] = round(p["proactivity"] - step, 3)
            changed.append(f"proactivity ↓ {p['proactivity']:.2f}")

    # ── Warmth ────────────────────────────────────
    if signals.get("wants_warmer"):
        if p["warmth"] < 0.9:
            p["warmth"] = round(p["warmth"] + step, 3)
            changed.append(f"warmth ↑ {p['warmth']:.2f}")

    if signals.get("wants_colder"):
        if p["warmth"] > 0.1:
            p["warmth"] = round(p["warmth"] - step, 3)
            changed.append(f"warmth ↓ {p['warmth']:.2f}")

    # ── Update tracking ───────────────────────────
    p["total_interactions"] += 1
    if signals.get("general_positive"):
        p["positive_reactions"] += 1
    if signals.get("general_negative"):
        p["negative_reactions"] += 1

    p["last_updated"] = datetime.datetime.now().isoformat()

    # Log evolution
    if changed:
        p["evolution_log"].append({
            "date":    datetime.date.today().isoformat(),
            "changes": changed,
            "signals": list(signals.keys())
        })
        p["evolution_log"] = p["evolution_log"][-50:]  # keep last 50
        print(f"[PersonalityEngine] Evolved: {', '.join(changed)}")

    _save(p)


# ─────────────────────────────────────────────────
# GET PERSONALITY PROMPT
# Returns instructions for LLM based on current personality
# ─────────────────────────────────────────────────

def get_personality_prompt() -> str:
    """
    Returns dynamic personality instructions for the LLM.
    Called every time a response is generated.
    This is what makes every response feel like Vivie.
    """
    p = _load()

    instructions = []

    # ── Response Length ───────────────────────────
    length = p["response_length"]
    if length < 0.3:
        instructions.append(
            "Keep responses extremely concise — 1-2 sentences maximum. "
            "User prefers very short answers."
        )
    elif length < 0.5:
        instructions.append(
            "Keep responses brief and to the point. "
            "Avoid unnecessary explanation."
        )
    elif length < 0.7:
        instructions.append(
            "Provide moderately detailed responses. "
            "Include key details but avoid padding."
        )
    else:
        instructions.append(
            "Provide comprehensive, detailed responses. "
            "User appreciates depth and thoroughness."
        )

    # ── Tone ──────────────────────────────────────
    tone = p["tone"]
    if tone < 0.3:
        instructions.append(
            "Maintain a formal, professional tone. "
            "Be precise and structured."
        )
    elif tone < 0.5:
        instructions.append(
            "Use a balanced professional tone. "
            "Friendly but not casual."
        )
    elif tone < 0.7:
        instructions.append(
            "Be conversational and natural. "
            "Occasional light humor is appropriate."
        )
    else:
        instructions.append(
            "Be casual, witty and very conversational. "
            "User enjoys humor and informal interaction."
        )

    # ── Technical Depth ───────────────────────────
    depth = p["technical_depth"]
    if depth < 0.3:
        instructions.append(
            "Use simple language. Avoid technical jargon. "
            "Explain concepts as if to a beginner."
        )
    elif depth < 0.6:
        instructions.append(
            "Balance technical accuracy with clarity. "
            "Explain terms when used."
        )
    else:
        instructions.append(
            "Use technical depth freely. "
            "User is technically advanced and appreciates precision."
        )

    # ── Warmth ────────────────────────────────────
    warmth = p["warmth"]
    if warmth < 0.3:
        instructions.append(
            "Maintain professional distance. "
            "Focus on task completion, minimal personal interaction."
        )
    elif warmth < 0.6:
        instructions.append(
            "Show measured warmth. "
            "Acknowledge the user personally when relevant."
        )
    else:
        instructions.append(
            "Be warm, personal and genuinely caring. "
            "Remember the user as an individual, not just a prompt."
        )

    # ── Personality Summary ───────────────────────
    profile = _describe_personality(p)

    prompt = (
        f"[Vivie's Current Personality Profile]\n"
        f"{profile}\n\n"
        f"[Active Behavioral Instructions]\n"
        + "\n".join(f"• {i}" for i in instructions)
    )

    return prompt


# ─────────────────────────────────────────────────
# DESCRIBE PERSONALITY
# Human readable personality description
# ─────────────────────────────────────────────────

def _describe_personality(p: dict) -> str:
    """Convert personality numbers to readable description."""

    length  = p["response_length"]
    tone    = p["tone"]
    depth   = p["technical_depth"]
    warmth  = p["warmth"]
    proact  = p["proactivity"]
    total   = p["total_interactions"]

    parts = []

    if length < 0.4:
        parts.append("concise")
    elif length > 0.6:
        parts.append("detailed")

    if tone > 0.6:
        parts.append("casual and witty")
    elif tone < 0.3:
        parts.append("formal")
    else:
        parts.append("balanced")

    if depth > 0.6:
        parts.append("technically deep")
    elif depth < 0.3:
        parts.append("accessible")

    if warmth > 0.6:
        parts.append("warm and personal")
    elif warmth < 0.3:
        parts.append("professional")

    style = ", ".join(parts) if parts else "neutral"

    return (
        f"After {total} interactions, Vivie has evolved to be: {style}. "
        f"This personality was shaped entirely by this specific user's preferences."
    )


# ─────────────────────────────────────────────────
# GET PERSONALITY STATUS
# For displaying in UI or asking Vivie about herself
# ─────────────────────────────────────────────────

def get_personality_status() -> str:
    """
    Returns a human-readable personality status.
    Vivie can describe herself using this.
    """
    p = _load()

    status  = f"I've had {p['total_interactions']} interactions with you. "
    status += f"Based on your feedback, I've evolved to be:\n\n"

    dims = [
        ("Response Style", p["response_length"],
         ["Very Brief", "Brief", "Balanced", "Detailed", "Very Detailed"]),
        ("Tone",           p["tone"],
         ["Very Formal", "Formal", "Balanced", "Casual", "Very Casual"]),
        ("Technical Depth", p["technical_depth"],
         ["Very Simple", "Simple", "Balanced", "Technical", "Very Technical"]),
        ("Warmth",         p["warmth"],
         ["Professional", "Measured", "Balanced", "Warm", "Very Warm"]),
        ("Proactivity",    p["proactivity"],
         ["Passive", "Reserved", "Balanced", "Proactive", "Very Proactive"]),
    ]

    for name, value, labels in dims:
        idx   = min(4, int(value * 5))
        label = labels[idx]
        bar   = "█" * int(value * 10) + "░" * (10 - int(value * 10))
        status += f"  {name:<18} [{bar}] {label}\n"

    total     = p["positive_reactions"] + p["negative_reactions"]
    if total > 0:
        sat = int(p["positive_reactions"] / total * 100)
        status += f"\nSatisfaction rate: {sat}% positive reactions."

    return status


# ─────────────────────────────────────────────────
# RECORD PROACTIVITY CHECK
# Updates proactivity check interval based on setting
# ─────────────────────────────────────────────────

def get_proactivity_interval() -> int:
    """
    Returns check interval in seconds based on proactivity setting.
    High proactivity = checks more often.
    """
    p     = _load()
    level = p["proactivity"]

    if level < 0.2:
        return 3600      # 1 hour
    elif level < 0.4:
        return 1800      # 30 min
    elif level < 0.6:
        return 1200      # 20 min
    elif level < 0.8:
        return 600       # 10 min
    else:
        return 300       # 5 min