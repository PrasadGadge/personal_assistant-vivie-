# ==========================================
# context.py — Updated with Persistent Memory
# ==========================================

import time
import os
from collections import deque
from memory_core.session_memory import get_session_memory


class ContextManager:

    def __init__(self, max_history=6):
        self.max_history = max_history
        self.reset()

    def reset(self):
        self.primary_entity = None
        self.entity_type    = None
        self.topic          = None
        self.history        = deque(maxlen=self.max_history)
        self.timestamp      = None
        self.pending_action = None
        self.pending_data   = {}

    def update(self, intent: dict, user_text: str, response: str):
        self.timestamp = time.time()

        self.history.append({
            "user":      user_text,
            "assistant": response
        })

        self.last_intent = intent.get("primary")
        entity      = intent.get("entity")
        entity_type = intent.get("entity_type")

        if entity:
            self.primary_entity = entity
            self.entity_type    = entity_type

        if intent.get("subtype"):
            self.topic = intent.get("subtype")

        # ✅ Persist to session memory
        try:
            session = get_session_memory()
            session.add_turn(
                user_input = user_text,
                response   = response,
                intent     = intent.get("primary", "chat")
            )
        except Exception:
            pass

    def set_pending_action(self, action_type, data=None):
        self.pending_action = action_type
        self.pending_data   = data if data else {}
        self.timestamp      = time.time()

        # ✅ Save unfinished task
        try:
            session = get_session_memory()
            session.set_unfinished_task(action_type)
        except Exception:
            pass

    def clear_pending_action(self):
        self.pending_action = None
        self.pending_data   = {}

        # ✅ Clear unfinished task
        try:
            session = get_session_memory()
            session.clear_unfinished_task()
        except Exception:
            pass

    def has_pending_action(self):
        return self.pending_action is not None

    def is_expired(self, expiry_seconds=180):
        if not self.timestamp:
            return True
        return (time.time() - self.timestamp) > expiry_seconds

    def build_context_prompt(self, current_user_input: str) -> str:
        if self.is_expired():
            self.history.clear()

        history_text = ""
        for turn in self.history:
            u = turn['user'][:100]
            a = turn['assistant'][:150].split('\n')[0]  # first line only, no nested prompts
            history_text += f"User: {u}\nAssistant: {a}\n"

        # ✅ Inject previous session context
        prev_context = ""
        try:
            session      = get_session_memory()
            prev_context = session.get_previous_context(turns_back=3)
        except Exception:
            pass

        context_block = f"""
Previous Conversation Context:

Primary Entity:  {self.primary_entity}
Entity Type:     {self.entity_type}
Current Topic:   {self.topic}
Pending Action:  {self.pending_action}

Recent Conversation:
{history_text}
"""
        if prev_context:
            context_block += f"\n{prev_context}\n"

        context_block += f"""
User now asks:
{current_user_input}

Instructions:
- If this relates to pending action, continue it.
- If unrelated, ignore old context.
- Answer clearly and naturally.
"""
        return context_block.strip()