# ==================================================
# session_memory.py — Vivie Continuous Memory
# Persists full context across sessions and days
# ==================================================

import json
import os
import time
import datetime
from collections import deque

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE  = os.path.join(BASE_DIR, "data", "session_memory.json")
MAX_TURNS     = 20   # max conversation turns to persist
MAX_SESSIONS  = 7    # keep last 7 sessions


# ─────────────────────────────────────────────────
# LOAD / SAVE
# ─────────────────────────────────────────────────

def _load_session_data() -> dict:
    if not os.path.exists(SESSION_FILE):
        return {
            "sessions":       [],
            "current_session": None,
            "last_topic":     None,
            "last_entity":    None,
            "unfinished_task": None
        }
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "sessions":        [],
            "current_session": None,
            "last_topic":      None,
            "last_entity":     None,
            "unfinished_task": None
        }


def _save_session_data(data: dict):
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SessionMemory] Save error: {e}")


# ─────────────────────────────────────────────────
# SESSION MANAGER
# ─────────────────────────────────────────────────

class SessionMemory:
    """
    Persistent session memory that survives restarts.
    Stores conversations, topics, and unfinished tasks.
    """

    def __init__(self):
        self._data           = _load_session_data()
        self._session_start  = datetime.datetime.now().isoformat()
        self._current_turns  = []
        self._start_new_session()

    def _start_new_session(self):
        """Start a new session entry."""
        session = {
            "id":        len(self._data["sessions"]) + 1,
            "start":     self._session_start,
            "end":       None,
            "turns":     [],
            "topics":    [],
            "summary":   ""
        }
        self._data["sessions"].append(session)

        # Keep only last MAX_SESSIONS
        if len(self._data["sessions"]) > MAX_SESSIONS:
            self._data["sessions"] = self._data["sessions"][-MAX_SESSIONS:]

        _save_session_data(self._data)
        print(f"[SessionMemory] New session started (#{session['id']})")

    def add_turn(self, user_input: str, response: str, intent: str = "chat"):
        """Add a conversation turn to current session."""
        try:
            turn = {
                "time":       datetime.datetime.now().strftime("%H:%M"),
                "user":       user_input[:200],
                "assistant":  response[:400],
                "intent":     intent
            }

            self._current_turns.append(turn)

            # Update current session
            if self._data["sessions"]:
                current = self._data["sessions"][-1]
                current["turns"] = self._current_turns[-MAX_TURNS:]

                # Track topics
                if intent not in ["chat", "unknown"] and intent not in current["topics"]:
                    current["topics"].append(intent)

            # Update last topic and entity
            self._data["last_topic"]  = intent
            self._data["last_entity"] = user_input[:80]

            _save_session_data(self._data)

        except Exception as e:
            print(f"[SessionMemory] Add turn error: {e}")

    def set_unfinished_task(self, task: str):
        """Mark something as unfinished for next session."""
        try:
            self._data["unfinished_task"] = {
                "task":    task,
                "time":    datetime.datetime.now().isoformat(),
                "session": len(self._data["sessions"])
            }
            _save_session_data(self._data)
        except Exception as e:
            print(f"[SessionMemory] Set unfinished task error: {e}")

    def clear_unfinished_task(self):
        """Clear unfinished task once completed."""
        self._data["unfinished_task"] = None
        _save_session_data(self._data)

    def get_session_greeting(self) -> str:
        """
        Generate a Jarvis-style greeting based on last session.
        Returns empty string if no previous session exists.
        """
        try:
            sessions = self._data["sessions"]

            # Need at least 2 sessions (current + previous)
            if len(sessions) < 2:
                return ""

            # Get previous session (second to last)
            prev = sessions[-2]
            turns = prev.get("turns", [])

            if not turns:
                return ""

            # Build greeting
            parts = []
            now   = datetime.datetime.now()

            # Time-based greeting
            hour = now.hour
            if 5 <= hour < 12:
                greeting = "Good morning Boss."
            elif 12 <= hour < 17:
                greeting = "Good afternoon Boss."
            elif 17 <= hour < 21:
                greeting = "Good evening Boss."
            else:
                greeting = "Welcome back Boss."

            parts.append(greeting)

            # Last session summary
            last_turn = turns[-1]
            last_topic = last_turn.get("intent", "")
            last_input = last_turn.get("user", "")

            if last_input:
                parts.append(
                    f"Last time we discussed: {last_input[:60]}."
                )

            # Unfinished task
            unfinished = self._data.get("unfinished_task")
            if unfinished:
                task = unfinished.get("task", "")
                if task:
                    parts.append(
                        f"You had an unfinished task: {task}. "
                        f"Want to continue?"
                    )

            # Topics from last session
            topics = prev.get("topics", [])
            if topics and len(topics) > 0:
                topic_str = ", ".join(topics[:3])
                parts.append(f"Previous session covered: {topic_str}.")

            return " ".join(parts)

        except Exception as e:
            print(f"[SessionMemory] Greeting error: {e}")
            return ""

    def get_previous_context(self, turns_back: int = 5) -> str:
        """
        Get recent conversation context from previous sessions.
        Used to inject into LLM prompt for continuity.
        """
        try:
            sessions = self._data["sessions"]
            if len(sessions) < 2:
                return ""

            # Get last few turns from previous session
            prev  = sessions[-2]
            turns = prev.get("turns", [])[-turns_back:]

            if not turns:
                return ""

            lines = ["Previous session context:"]
            for turn in turns:
                lines.append(f"[{turn['time']}] User: {turn['user']}")
                lines.append(f"[{turn['time']}] Vivie: {turn['assistant'][:150]}")

            return "\n".join(lines)

        except Exception as e:
            print(f"[SessionMemory] Previous context error: {e}")
            return ""

    def get_session_stats(self) -> dict:
        """Return stats about all sessions."""
        try:
            sessions = self._data["sessions"]
            total_turns = sum(
                len(s.get("turns", [])) for s in sessions
            )
            return {
                "total_sessions": len(sessions),
                "total_turns":    total_turns,
                "last_topic":     self._data.get("last_topic", ""),
                "has_unfinished": self._data.get("unfinished_task") is not None
            }
        except Exception:
            return {}

    def end_session(self):
        """Call when Vivie shuts down — saves session summary."""
        try:
            if not self._data["sessions"]:
                return

            current = self._data["sessions"][-1]
            current["end"] = datetime.datetime.now().isoformat()

            # Simple summary
            turns = current.get("turns", [])
            if turns:
                topics  = current.get("topics", [])
                summary = f"Session with {len(turns)} turns."
                if topics:
                    summary += f" Topics: {', '.join(topics[:3])}."
                current["summary"] = summary

            _save_session_data(self._data)
            print("[SessionMemory] Session saved.")

        except Exception as e:
            print(f"[SessionMemory] End session error: {e}")


# ─────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────

_session: SessionMemory = None


def get_session_memory() -> SessionMemory:
    global _session
    if _session is None:
        _session = SessionMemory()
    return _session