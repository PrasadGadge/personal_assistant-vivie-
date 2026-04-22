# ==================================================
# behavior_engine.py — Vivie Behavioral Pattern Learning
# Learns your daily habits and anticipates your needs
# ==================================================

import json
import os
import threading
import time
import datetime
from collections import defaultdict

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERNS_FILE = os.path.join(BASE_DIR, "data", "behavior_patterns.json")
MIN_DAYS      = 2    # minimum days before suggesting a pattern
MIN_COUNT     = 2    # minimum occurrences before it's a pattern


# ─────────────────────────────────────────────────
# LOAD / SAVE
# ─────────────────────────────────────────────────

def _load_patterns() -> dict:
    if not os.path.exists(PATTERNS_FILE):
        return {}
    try:
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_patterns(data: dict):
    try:
        os.makedirs(os.path.dirname(PATTERNS_FILE), exist_ok=True)
        with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[BehaviorEngine] Save error: {e}")


# ─────────────────────────────────────────────────
# RECORD BEHAVIOR
# Called every time user does something
# ─────────────────────────────────────────────────

def record_behavior(action: str, context: str = ""):
    """
    Record what the user did at what time.

    Args:
        action:  what they did ("opened youtube", "asked about python")
        context: extra context (intent, topic, etc.)
    """
    try:
        now     = datetime.datetime.now()
        hour    = now.hour
        weekday = now.strftime("%A")  # Monday, Tuesday etc
        date    = now.date().isoformat()

        patterns = _load_patterns()

        # Build time slot — group by hour
        slot = f"{hour:02d}:00"

        # Key = action + time slot
        key = f"{action}|{slot}"

        if key not in patterns:
            patterns[key] = {
                "action":    action,
                "slot":      slot,
                "hour":      hour,
                "context":   context,
                "count":     0,
                "days":      [],
                "weekdays":  [],
                "last_seen": ""
            }

        entry = patterns[key]
        entry["count"] += 1
        entry["last_seen"] = now.isoformat()

        if date not in entry["days"]:
            entry["days"].append(date)
            # Keep last 30 days only
            entry["days"] = entry["days"][-30:]

        if weekday not in entry["weekdays"]:
            entry["weekdays"].append(weekday)

        _save_patterns(patterns)

    except Exception as e:
        print(f"[BehaviorEngine] Record error: {e}")


# ─────────────────────────────────────────────────
# GET CURRENT SUGGESTIONS
# What should Vivie suggest right now?
# ─────────────────────────────────────────────────

def get_suggestions(top_k: int = 3) -> list:
    """
    Returns list of suggestions based on current time.

    Returns list of dicts:
    [{"action": "open youtube", "message": "You usually watch YouTube at this time.", "confidence": 0.8}]
    """
    try:
        now     = datetime.datetime.now()
        hour    = now.hour
        slot    = f"{hour:02d}:00"
        weekday = now.strftime("%A")

        patterns  = _load_patterns()
        suggestions = []

        for key, entry in patterns.items():
            if entry["slot"] != slot:
                continue

            count      = entry["count"]
            unique_days = len(entry["days"])

            # Must meet minimum threshold
            if count < MIN_COUNT or unique_days < MIN_DAYS:
                continue

            # Calculate confidence
            confidence = min(0.95, 0.5 + (unique_days / 14) * 0.45)

            # Build natural message
            action  = entry["action"]
            message = _build_suggestion_message(action, count, weekday, entry["weekdays"])

            suggestions.append({
                "action":     action,
                "message":    message,
                "confidence": round(confidence, 2),
                "count":      count,
                "days":       unique_days
            })

        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:top_k]

    except Exception as e:
        print(f"[BehaviorEngine] Suggestions error: {e}")
        return []


# ─────────────────────────────────────────────────
# GET PATTERN SUMMARY
# For Vivie to describe your habits
# ─────────────────────────────────────────────────

def get_pattern_summary() -> str:
    """
    Returns a human-readable summary of learned patterns.
    Vivie can use this to tell you what she knows about you.
    """
    try:
        patterns = _load_patterns()
        if not patterns:
            return "I haven't learned your patterns yet. Keep using me and I'll adapt."

        strong = [
            e for e in patterns.values()
            if e["count"] >= MIN_COUNT and len(e["days"]) >= MIN_DAYS
        ]

        if not strong:
            return "I'm still learning your habits. Give me a few more days."

        lines = ["Here's what I've learned about your patterns:"]
        for entry in strong[:5]:
            action  = entry["action"]
            slot    = entry["slot"]
            days    = len(entry["days"])
            lines.append(f"  • You usually {action} around {slot} ({days} days observed)")

        return "\n".join(lines)

    except Exception as e:
        return "Unable to retrieve pattern summary."


# ─────────────────────────────────────────────────
# ANALYZE MOST ACTIVE HOURS
# ─────────────────────────────────────────────────

def get_active_hours() -> dict:
    """
    Returns which hours user is most active.
    Useful for scheduling, proactive checks.
    """
    try:
        patterns  = _load_patterns()
        hour_counts = defaultdict(int)

        for entry in patterns.values():
            hour_counts[entry["hour"]] += entry["count"]

        if not hour_counts:
            return {}

        # Return top 5 active hours
        sorted_hours = sorted(
            hour_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return dict(sorted_hours[:5])

    except Exception:
        return {}


# ─────────────────────────────────────────────────
# HELPER — Build natural suggestion message
# ─────────────────────────────────────────────────

def _build_suggestion_message(action: str, count: int, current_weekday: str, seen_weekdays: list) -> str:
    """Build a natural Jarvis-style suggestion message."""

    # Weekday pattern
    if len(seen_weekdays) >= 5:
        weekday_str = "most days"
    elif len(seen_weekdays) >= 3:
        weekday_str = "several days a week"
    elif current_weekday in seen_weekdays:
        weekday_str = f"on {current_weekday}s"
    else:
        weekday_str = "regularly"

    # Action cleanup
    action_clean = action.replace("_", " ").replace("opened", "open")

    templates = [
        f"You usually {action_clean} at this time {weekday_str}.",
        f"Based on your habits, you tend to {action_clean} around now.",
        f"You've {action_clean} at this hour {count} times before.",
    ]

    import random
    return random.choice(templates)


# ─────────────────────────────────────────────────
# PROACTIVE MONITOR
# Background thread that checks patterns every 5 min
# ─────────────────────────────────────────────────

_last_spoken_hour = -1


def _pattern_monitor():
    """
    Background thread.
    Checks every 5 minutes if there's a strong pattern to suggest.
    Only speaks once per hour to avoid being annoying.
    """
    global _last_spoken_hour

    print("[BehaviorEngine] Pattern monitor started.")

    while True:
        try:
            now  = datetime.datetime.now()
            hour = now.hour

            # Only once per hour
            if hour != _last_spoken_hour:
                suggestions = get_suggestions(top_k=1)

                if suggestions:
                    best = suggestions[0]

                    # Only suggest high confidence patterns
                    if best["confidence"] >= 0.65:
                        try:
                            from TextToSpeech.Fast_DF_TTS import speak
                            from voice_state import speak_lock, set_speaking, is_speaking as voice_is_speaking, wait_until_done

                            msg = f"Boss, {best['message']}"

                            with speak_lock:
                                speak(msg)

                            _last_spoken_hour = hour

                            # Update UI proactive panel
                            try:
                                from Vivie_UI import get_ui
                                ui = get_ui()
                                if ui:
                                    from Core_structure.tool_manifest import get_all_tools
                                    pass  # UI update handled by proactive engine
                            except Exception:
                                pass

                            print(f"[BehaviorEngine] Suggested: {best['action']}")

                        except Exception as e:
                            print(f"[BehaviorEngine] Speak error: {e}")

        except Exception as e:
            print(f"[BehaviorEngine] Monitor error: {e}")

        time.sleep(300)  # Check every 5 minutes


def start_behavior_engine():
    """Start the pattern monitor in background."""
    t = threading.Thread(target=_pattern_monitor, daemon=True)
    t.start()
    print("[BehaviorEngine] Engine started.")