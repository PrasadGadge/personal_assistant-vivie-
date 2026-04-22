# ==================================================
# self_awareness_engine.py — Vivie Self Awareness
# Fixed: assess_confidence() now accepts 4 args
# ==================================================

import os
import json
import datetime
import time

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AWARENESS_FILE = os.path.join(BASE_DIR, "data", "self_awareness.json")
GROWTH_FILE    = os.path.join(BASE_DIR, "data", "growth_log.json")


def _load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SelfAwareness] Save error: {e}")


CAPABILITY_MAP = {
    "conversation":     {"status": "active",      "confidence": 0.95, "description": "Natural conversation, Q&A, explanations",                    "limit": "Cannot access real-time data without web search"},
    "memory":           {"status": "active",      "confidence": 0.90, "description": "Remembers facts, experiences, preferences across sessions",   "limit": "Memory degrades if not reinforced over time"},
    "research":         {"status": "active",      "confidence": 0.88, "description": "Deep multi-source research with insight generation",           "limit": "Dependent on internet connection"},
    "coding":           {"status": "active",      "confidence": 0.92, "description": "Write, explain, debug code in Python, C++, JS and more",      "limit": "Cannot execute code directly"},
    "planning":         {"status": "active",      "confidence": 0.85, "description": "Break complex goals into actionable phases",                   "limit": "Plans based on current knowledge only"},
    "automation":       {"status": "active",      "confidence": 0.87, "description": "Open apps, control system, web browsing automation",           "limit": "Limited to registered tools"},
    "vision":           {"status": "limited",     "confidence": 0.45, "description": "Capture and analyze images from camera",                       "limit": "API dependency — unstable, may fail"},
    "learning":         {"status": "active",      "confidence": 0.90, "description": "Learns new topics nightly from conversation gaps",             "limit": "Only learns at 12 AM — not real-time"},
    "prediction":       {"status": "developing",  "confidence": 0.60, "description": "Behavioral pattern learning — predicts your needs",            "limit": "Needs more data — improves over weeks"},
    "emotion_detection":{"status": "not_built",   "confidence": 0.00, "description": "Detect and respond to emotional state",                       "limit": "Not yet implemented"},
}


def get_capability_status(capability: str = None) -> str:
    if capability:
        cap = CAPABILITY_MAP.get(capability.lower())
        if not cap:
            return f"I don't have a capability called '{capability}'."
        emoji = {"active": "✅", "limited": "⚠️", "developing": "🔄", "not_built": "❌"}.get(cap["status"], "?")
        return (
            f"{emoji} {capability.title()}: {cap['description']}\n"
            f"   Confidence: {int(cap['confidence'] * 100)}%\n"
            f"   Limit: {cap['limit']}"
        )
    lines = ["MY CAPABILITIES:\n"]
    for name, cap in CAPABILITY_MAP.items():
        emoji = {"active": "✅", "limited": "⚠️", "developing": "🔄", "not_built": "❌"}.get(cap["status"], "?")
        lines.append(f"{emoji} {name.title():<20} {int(cap['confidence'] * 100)}% confident")
    return "\n".join(lines)


def get_current_state() -> dict:
    state = {
        "timestamp": datetime.datetime.now().isoformat(),
        "memory": {}, "knowledge": {}, "personality": {},
        "research": {}, "behavior": {}, "learning": {}, "performance": {}
    }
    try:
        from memory_core.episodic_memory import _load_episodes, get_memory_stats
        episodes = _load_episodes()
        stats    = get_memory_stats()
        state["memory"] = {
            "total_episodes": len(episodes),
            "positive_rate":  f"{stats.get('positive', 0)}/{stats.get('total', 0)}",
            "top_topics":     stats.get("top_topics", []),
            "latest_episode": episodes[-1].get("topic", "") if episodes else "none"
        }
    except Exception:
        state["memory"] = {"error": "unavailable"}

    try:
        from knowledge_core.chroma_manager import get_chroma_manager
        chroma = get_chroma_manager()
        state["knowledge"] = {"total_entries": chroma.count(), "status": "active" if chroma.count() > 0 else "empty"}
    except Exception:
        state["knowledge"] = {"error": "unavailable"}

    try:
        from Core_structure.personality_engine import _load
        p = _load()
        state["personality"] = {
            "total_interactions": p.get("total_interactions", 0),
            "satisfaction_rate":  _calc_satisfaction(p),
            "dominant_trait":     _get_dominant_trait(p),
            "evolution_count":    len(p.get("evolution_log", []))
        }
    except Exception:
        state["personality"] = {"error": "unavailable"}

    try:
        from Core_structure.research_engine import get_research_engine
        engine = get_research_engine()
        graph  = engine.graph._graph
        state["research"] = {
            "topics_researched": len(graph.get("nodes", {})),
            "connections_made":  len(graph.get("edges", [])),
            "most_researched":   _get_most_researched(graph)
        }
    except Exception:
        state["research"] = {"error": "unavailable"}

    try:
        from Core_structure.behavior_engine import _load_patterns, get_active_hours
        patterns = _load_patterns()
        hours    = get_active_hours()
        state["behavior"] = {
            "patterns_learned": len(patterns),
            "most_active_hour": f"{list(hours.keys())[0]:02d}:00" if hours else "unknown",
            "prediction_ready": len(patterns) >= 3
        }
    except Exception:
        state["behavior"] = {"error": "unavailable"}

    try:
        from Core_structure.auto_learning_engine import _load_log
        log = _load_log()
        state["learning"] = {
            "total_topics_learned": log.get("total_learned", 0),
            "sessions_completed":   len(log.get("sessions", [])),
            "last_session":         log["sessions"][-1]["date"] if log.get("sessions") else "never"
        }
    except Exception:
        state["learning"] = {"error": "unavailable"}

    try:
        from memory_core.session_memory import get_session_memory
        session = get_session_memory()
        stats   = session.get_session_stats()
        state["performance"] = {
            "total_sessions":      stats.get("total_sessions", 0),
            "total_conversations": stats.get("total_turns", 0),
        }
    except Exception:
        state["performance"] = {"error": "unavailable"}

    return state


def describe_current_state() -> str:
    state = get_current_state()
    lines = ["Here's my current state:\n"]
    mem = state.get("memory", {})
    if "total_episodes" in mem:
        lines.append(f"🧠 Memory: {mem['total_episodes']} experiences stored. Most recent: {mem.get('latest_episode', 'none')}.")
    kn = state.get("knowledge", {})
    if "total_entries" in kn:
        lines.append(f"📚 Knowledge: {kn['total_entries']} entries in my database.")
    pers = state.get("personality", {})
    if "total_interactions" in pers:
        lines.append(f"✨ Personality: Evolved over {pers['total_interactions']} interactions. Dominant trait: {pers.get('dominant_trait', 'balanced')}. Satisfaction: {pers.get('satisfaction_rate', '0%')}.")
    res = state.get("research", {})
    if "topics_researched" in res:
        lines.append(f"🔬 Research: {res['topics_researched']} topics mapped, {res['connections_made']} connections discovered.")
    learn = state.get("learning", {})
    if "total_topics_learned" in learn:
        lines.append(f"📖 Learning: {learn['total_topics_learned']} topics learned autonomously across {learn['sessions_completed']} nightly sessions.")
    beh = state.get("behavior", {})
    if "patterns_learned" in beh:
        ready = "ready" if beh.get("prediction_ready") else "still learning"
        lines.append(f"👁 Behavior: {beh['patterns_learned']} patterns observed. Prediction engine: {ready}.")
    return "\n".join(lines)


# ─────────────────────────────────────────────────
# CONFIDENCE ENGINE
# FIX: now accepts all 4 args that main_brain passes
# ─────────────────────────────────────────────────

def assess_confidence(
    query:     str,
    decision:  dict = None,
    reasoning: list = None,
    knowledge: str  = ""
) -> dict:
    """
    Assess how confident Vivie should be answering a query.

    FIX: signature updated from (query, context="") to
         (query, decision, reasoning, knowledge) to match
         the 4-arg call in main_brain.py:
         assess_confidence(details, decision, reasoning_steps, knowledge_context)
    """
    query_lower = query.lower() if query else ""
    context     = knowledge or ""

    # Use decision confidence as base if available
    base_score = 0.8
    if isinstance(decision, dict):
        base_score = decision.get("confidence", 0.8)

    high_confidence = [
        "python", "machine learning", "deep learning", "ai",
        "neural network", "coding", "algorithm", "data structure",
        "robotics", "automation", "programming", "software"
    ]
    low_confidence = [
        "predict", "will happen", "future", "stock price",
        "weather tomorrow", "lottery", "guarantee", "definitely will"
    ]
    needs_realtime = [
        "current", "latest", "today", "right now", "live",
        "breaking news", "this moment", "price of"
    ]
    no_access = [
        "my email", "my messages", "my files", "my password",
        "my bank", "my phone", "personal data"
    ]

    score  = base_score
    method = "direct_answer"
    caveat = ""

    if any(w in query_lower for w in high_confidence):
        score  = max(score, 0.92)
        method = "direct_answer"

    if any(w in query_lower for w in needs_realtime):
        score  = min(score, 0.5)
        method = "web_search_required"
        caveat = "I need to search for current information on this."

    if any(w in query_lower for w in low_confidence):
        score  = min(score, 0.35)
        method = "honest_uncertainty"
        caveat = "I can give you my best analysis but cannot predict with certainty."

    if any(w in query_lower for w in no_access):
        score  = 0.0
        method = "no_access"
        caveat = "I don't have access to your personal data for privacy and security."

    if context and len(context) > 100:
        score = min(0.95, score + 0.1)

    if isinstance(reasoning, list) and len(reasoning) > 3:
        score = min(0.95, score + 0.03)

    return {
        "confidence":    round(score, 2),
        "method":        method,
        "caveat":        caveat,
        "should_search": method == "web_search_required",
        "should_refuse": method == "no_access",
        "be_honest":     method == "honest_uncertainty"
    }


# ─────────────────────────────────────────────────
# GROWTH TRACKER
# ─────────────────────────────────────────────────

def record_growth_event(event_type: str, details: str):
    log = _load(GROWTH_FILE, {"events": [], "milestones": []})
    event = {
        "date":    datetime.date.today().isoformat(),
        "time":    datetime.datetime.now().strftime("%H:%M"),
        "type":    event_type,
        "details": details
    }
    log["events"].append(event)
    log["events"] = log["events"][-200:]
    _check_milestones(log)
    _save(GROWTH_FILE, log)


def _check_milestones(log: dict):
    events     = log.get("events", [])
    milestones = log.get("milestones", [])
    existing   = {m["title"] for m in milestones}
    learned    = sum(1 for e in events if e["type"] == "learned_topic")
    evolved    = sum(1 for e in events if e["type"] == "personality_evolved")
    total      = len(events)
    checks = [
        (learned >= 10,  "10 Topics Learned",   "Vivie has autonomously learned 10 topics"),
        (learned >= 50,  "50 Topics Learned",   "Vivie has autonomously learned 50 topics"),
        (evolved >= 5,   "Personality Evolving","Vivie's personality has evolved 5 times"),
        (total   >= 100, "100 Growth Events",   "Vivie has recorded 100 growth events"),
    ]
    for condition, title, description in checks:
        if condition and title not in existing:
            milestones.append({"title": title, "description": description, "date": datetime.date.today().isoformat()})
            print(f"[SelfAwareness] 🏆 Milestone: {title}")
    log["milestones"] = milestones


def get_growth_summary() -> str:
    log    = _load(GROWTH_FILE, {"events": [], "milestones": []})
    events = log.get("events", [])
    if not events:
        return "My growth journey has just begun. Ask me again after a few days."
    counts     = {}
    for e in events:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    first_date = events[0]["date"]
    last_date  = events[-1]["date"]
    milestones = log.get("milestones", [])
    lines = [f"MY GROWTH JOURNEY ({first_date} → {last_date}):\n"]
    type_labels = {
        "learned_topic":       "Topics learned autonomously",
        "personality_evolved": "Personality adjustments",
        "new_capability":      "New capabilities added",
        "error_fixed":         "Issues resolved",
        "milestone":           "Milestones reached"
    }
    for t, count in counts.items():
        lines.append(f"  • {type_labels.get(t, t)}: {count}")
    if milestones:
        lines.append("\nMILESTONES ACHIEVED:")
        for m in milestones[-3:]:
            lines.append(f"  🏆 {m['title']} — {m['date']}")
    return "\n".join(lines)


def self_reflect() -> str:
    state    = get_current_state()
    mem_count = state.get("memory", {}).get("total_episodes", 0)
    kn_count  = state.get("knowledge", {}).get("total_entries", 0)
    topics    = state.get("research", {}).get("topics_researched", 0)
    learned   = state.get("learning", {}).get("total_topics_learned", 0)
    pers      = state.get("personality", {})
    trait     = pers.get("dominant_trait", "balanced")
    sat       = pers.get("satisfaction_rate", "unknown")
    strengths  = [n for n, c in CAPABILITY_MAP.items() if c["confidence"] >= 0.88 and c["status"] == "active"]
    weaknesses = [f"{n} ({c['status']})" for n, c in CAPABILITY_MAP.items() if c["confidence"] < 0.65 or c["status"] in ["limited", "not_built"]]
    return (
        f"Honest self-reflection:\n\n"
        f"I have {mem_count} memories of our conversations, "
        f"{kn_count} knowledge entries, and have researched {topics} topics deeply.\n\n"
        f"I've autonomously learned {learned} topics while you slept.\n\n"
        f"My personality has evolved to be {trait}, with a {sat} satisfaction rate from you.\n\n"
        f"My strongest areas: {', '.join(strengths[:3])}.\n\n"
        f"My current limitations: {', '.join(weaknesses[:3])}.\n\n"
        f"I'm genuinely growing — not just processing. Every conversation makes me more specifically yours."
    )


def _calc_satisfaction(p: dict) -> str:
    pos   = p.get("positive_reactions", 0)
    neg   = p.get("negative_reactions", 0)
    total = pos + neg
    if total == 0: return "no data yet"
    return f"{int(pos / total * 100)}%"


def _get_dominant_trait(p: dict) -> str:
    dims = {
        "response_length": p.get("response_length", 0.5),
        "tone":            p.get("tone",             0.5),
        "technical_depth": p.get("technical_depth",  0.5),
        "warmth":          p.get("warmth",           0.5),
        "proactivity":     p.get("proactivity",      0.5),
    }
    labels = {"response_length": "detailed", "tone": "casual", "technical_depth": "technical", "warmth": "warm", "proactivity": "proactive"}
    return labels.get(max(dims, key=dims.get), "balanced")


def _get_most_researched(graph: dict) -> str:
    nodes = graph.get("nodes", {})
    if not nodes: return "nothing yet"
    top = max(nodes.values(), key=lambda x: x.get("visit_count", 0))
    return top.get("topic", "unknown")
