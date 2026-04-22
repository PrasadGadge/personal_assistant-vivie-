# ==================================================
# episodic_memory.py — Vivie's Experience Memory
# Stores what happened, when, and what worked.
# ==================================================

import json
import os
from datetime import datetime,date

# ── Storage Path ──────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
EPISODES_FILE  = os.path.join(BASE_DIR, "episodes.json")

# ── Max episodes to keep (prevents file bloat) ────
MAX_EPISODES = 500


# ─────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────

def _load_episodes() -> list:
    if not os.path.exists(EPISODES_FILE):
        return []
    try:
        with open(EPISODES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ─────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────

def _save_episodes(episodes: list):
    try:
        # Keep only latest MAX_EPISODES
        if len(episodes) > MAX_EPISODES:
            episodes = episodes[-MAX_EPISODES:]
        with open(EPISODES_FILE, "w", encoding="utf-8") as f:
            json.dump(episodes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[EpisodicMemory] Save error: {e}")

# ─────────────────────────────────────────────────
# AUTO DETECT REACTION
# ─────────────────────────────────────────────────

def _auto_detect_reaction(user_input: str, vivie_response: str) -> str:
    """
    Automatically detect if response was good or bad
    based on conversation signals — no user input needed.
    """
    user = user_input.lower().strip()

    # ── Explicit positive signals ──────────────────
    positive_signals = [
        "good", "great", "perfect", "correct", "exactly",
        "yes", "right", "nice", "awesome", "thanks",
        "thank you", "well done", "good answer", "that's right",
        "that's correct", "makes sense", "i see", "got it",
        "understood", "helpful", "amazing", "brilliant"
    ]
    if any(w in user for w in positive_signals):
        return "positive"

    # ── Explicit negative signals ──────────────────
    negative_signals = [
        "wrong", "incorrect", "no that's wrong", "not right",
        "bad answer", "that's wrong", "you're wrong",
        "not helpful", "useless", "terrible", "awful",
        "stop", "that's not what i asked", "you misunderstood"
    ]
    if any(w in user for w in negative_signals):
        return "negative"

    # ── Response quality signals ───────────────────
    response = vivie_response.lower()

    # Good response indicators
    if len(vivie_response.split()) > 30:
        return "positive"   # detailed response = likely good

    # Short vague responses = likely neutral/negative
    vague_responses = [
        "i don't know", "i'm not sure", "i cannot",
        "i don't have", "unfortunately", "i apologize"
    ]
    if any(w in response for w in vague_responses):
        return "negative"

    return "neutral"


# ─────────────────────────────────────────────────
# STORE EPISODE
# ─────────────────────────────────────────────────

def store_episode(
    user_input:     str,
    vivie_response: str,
    intent:         str = "general",
    reaction:       str = "neutral"
) -> bool:
    """
    Store a full experience episode.
    Auto-detects reaction from conversation tone.
    """
    try:
        episodes = _load_episodes()

        # ✅ Auto-detect reaction instead of waiting for user
        auto_reaction = _auto_detect_reaction(user_input, vivie_response)

        episode = {
            "date":           datetime.now().strftime("%Y-%m-%d"),
            "time":           datetime.now().strftime("%H:%M"),
            "user_input":     user_input,
            "vivie_response": vivie_response[:300],
            "intent":         intent,
            "reaction":       auto_reaction,  # ✅ auto detected
            "topic":          _extract_topic(user_input),
            "response_length": len(vivie_response.split())
        }

        episodes.append(episode)
        _save_episodes(episodes)
        return True

    except Exception as e:
        print(f"[EpisodicMemory] Store error: {e}")
        return False


# ─────────────────────────────────────────────────
# RETRIEVE RELEVANT EPISODES
# ─────────────────────────────────────────────────

def retrieve_episodes(query: str, top_k: int = 3) -> list:
    """
    Find past episodes relevant to current query.
    Simple keyword overlap — fast and lightweight.
    """
    try:
        episodes = _load_episodes()
        if not episodes:
            return []

        query_words = set(query.lower().split())

        scored = []
        for ep in episodes:
            ep_text  = f"{ep['user_input']} {ep['topic']} {ep['intent']}".lower()
            ep_words = set(ep_text.split())
            overlap  = len(query_words & ep_words)
            if overlap > 0:
                scored.append((overlap, ep))

        # Sort by relevance, return top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]

    except Exception as e:
        print(f"[EpisodicMemory] Retrieve error: {e}")
        return []


# ─────────────────────────────────────────────────
# FORMAT FOR PROMPT INJECTION
# ─────────────────────────────────────────────────

def get_episode_context(query: str, top_k: int = 2) -> str:
    """
    Returns formatted episode context ready to inject into LLM prompt.
    Only returns something if relevant episodes found.
    """
    try:
        episodes = retrieve_episodes(query, top_k=top_k)
        if not episodes:
            return ""

        lines = ["Past relevant experiences:"]
        for ep in episodes:
            lines.append(
                f"- On {ep['date']} user asked about '{ep['topic']}' "
                f"(intent: {ep['intent']}). "
                f"Response was {ep['reaction']}."
            )

        return "\n".join(lines)

    except Exception as e:
        print(f"[EpisodicMemory] Context error: {e}")
        return ""


# ─────────────────────────────────────────────────
# UPDATE REACTION (call when user says good/wrong)
# ─────────────────────────────────────────────────

def update_last_reaction(reaction: str):
    """
    Update the reaction of the most recent episode.
    Call this when user says 'good answer' or 'wrong' etc.

    reaction: 'positive' or 'negative'
    """
    try:
        episodes = _load_episodes()
        if not episodes:
            return

        episodes[-1]["reaction"] = reaction
        _save_episodes(episodes)
        print(f"[EpisodicMemory] Last episode marked: {reaction}")

    except Exception as e:
        print(f"[EpisodicMemory] Update reaction error: {e}")


# ─────────────────────────────────────────────────
# STATS (useful for debugging)
# ─────────────────────────────────────────────────

def get_memory_stats() -> dict:
    """Returns basic stats about episodic memory."""
    try:
        episodes = _load_episodes()
        if not episodes:
            return {"total": 0}

        topics    = [ep["topic"]    for ep in episodes]
        reactions = [ep["reaction"] for ep in episodes]

        return {
            "total":     len(episodes),
            "positive":  reactions.count("positive"),
            "negative":  reactions.count("negative"),
            "neutral":   reactions.count("neutral"),
            "top_topics": _top_items(topics, 3)
        }
    except Exception:
        return {"total": 0}


# ─────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────

def _extract_topic(text: str) -> str:
    """Extract short topic label from user input."""
    stop_words = {
        "what", "how", "why", "when", "where", "who",
        "is", "are", "the", "a", "an", "do", "does",
        "can", "could", "tell", "me", "about", "please",
        "vivie", "i", "my", "you", "your"
    }
    words = [
        w for w in text.lower().split()
        if w not in stop_words and len(w) > 2
    ]
    return " ".join(words[:4]) if words else "general"


def _top_items(items: list, n: int) -> list:
    """Return top n most frequent items."""
    from collections import Counter
    return [item for item, _ in Counter(items).most_common(n)]