# ==================================================
# Core_structure/decision_engine.py
# Vivie's Intelligence Core
# Fixed: decide() crash safety, None guards in
#        build_smart_prompt, knowledge scoring
# ==================================================

import re
from datetime import datetime


# Safe fallback returned when decide() itself crashes
_SAFE_DECISION = {
    "top_memories":    "",
    "top_knowledge":   "",
    "response_depth":  "medium",
    "response_style":  "conversational",
    "priority_action": "general_response",
    "use_web_search":  False,
    "confidence":      0.6,
    "reasoning_hint":  "Answer helpfully and clearly."
}


class DecisionEngine:

    def __init__(self):
        self.decision_history = []
        self.action_outcomes  = []

    # ─────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────────

    def decide(
        self,
        user_input:    str,
        intent:        dict,
        memory_block:  str,
        knowledge:     str,
        context:       str,
        reasoning:     list
    ) -> dict:
        """
        Core decision loop — 8 steps.
        FIX: entire method wrapped in try/except so a crash
        in any step returns a safe fallback instead of
        propagating up and killing the response pipeline.
        """
        # Sanitise inputs so steps never receive None
        user_input   = user_input   or ""
        memory_block = memory_block or ""
        knowledge    = knowledge    or ""
        context      = context      or ""
        reasoning    = reasoning    if isinstance(reasoning, list) else []
        intent       = intent       if isinstance(intent, dict)    else {}

        try:
            top_memories  = self._score_memories(user_input, memory_block)
            top_knowledge = self._score_knowledge(user_input, knowledge)
            depth         = self._decide_depth(user_input, intent)
            style         = self._decide_style(user_input, intent, reasoning)
            action        = self._decide_priority_action(user_input, intent, top_memories)
            use_web       = self._needs_web_search(user_input, knowledge)
            confidence    = self._calculate_confidence(intent, top_memories, top_knowledge)
            hint          = self._generate_reasoning_hint(user_input, action, depth, top_memories)

            decision = {
                "top_memories":    top_memories    or "",
                "top_knowledge":   top_knowledge   or "",
                "response_depth":  depth,
                "response_style":  style,
                "priority_action": action,
                "use_web_search":  use_web,
                "confidence":      confidence,
                "reasoning_hint":  hint,
            }

            self._track_decision(user_input, decision)
            return decision

        except Exception as e:
            print(f"[DecisionEngine] decide() crashed: {e} — returning safe fallback")
            return dict(_SAFE_DECISION)   # copy so callers can't mutate the default


    # ─────────────────────────────────────────────
    # STEP 1 — SCORE MEMORIES
    # ─────────────────────────────────────────────

    def _score_memories(self, query: str, memory_block: str, top_k: int = 3) -> str:
        if not memory_block or not memory_block.strip():
            return ""

        query_words = set(query.lower().split())

        lines = [
            line.strip()
            for line in memory_block.split('\n')
            if line.strip() and len(line.strip()) > 10
        ]
        if not lines:
            return ""

        personal_words = {
            "name", "like", "love", "study", "work",
            "live", "prefer", "interest", "hobby", "college"
        }

        scored = []
        for line in lines:
            line_words = set(line.lower().split())
            overlap    = len(query_words & line_words)
            boost      = 2 if (personal_words & line_words) else 0
            score      = overlap + boost
            if score > 0:
                scored.append((score, line))

        if not scored:
            return "\n".join(lines[:top_k])

        scored.sort(key=lambda x: x[0], reverse=True)
        return "\n".join(line for _, line in scored[:top_k])


    # ─────────────────────────────────────────────
    # STEP 2 — SCORE KNOWLEDGE
    # FIX: multi-separator splitting so different
    # knowledge formats all get scored properly
    # ─────────────────────────────────────────────

    def _score_knowledge(self, query: str, knowledge: str, top_k: int = 2) -> str:
        if not knowledge or not knowledge.strip():
            return ""

        query_words = set(query.lower().split())

        # FIX: try multiple separators — knowledge may use
        # '\n-', '\n\n', or just '\n' depending on the source
        raw = knowledge
        for sep in ['\n\n', '\n-', '\n']:
            parts = [e.strip() for e in raw.split(sep) if e.strip() and len(e.strip()) > 15]
            if len(parts) > 1:
                break
        else:
            # Nothing split cleanly — treat whole block as one entry
            parts = [raw.strip()] if raw.strip() else []

        if not parts:
            return ""

        scored = []
        for entry in parts:
            entry_words = set(entry.lower().split())
            overlap     = len(query_words & entry_words)
            if overlap > 0:
                scored.append((overlap, entry))

        if not scored:
            # No overlap but we have knowledge — return first entries
            return "\n".join(parts[:top_k])

        scored.sort(key=lambda x: x[0], reverse=True)
        return "\n- ".join(e for _, e in scored[:top_k])


    # ─────────────────────────────────────────────
    # STEP 3 — DECIDE RESPONSE DEPTH
    # ─────────────────────────────────────────────

    def _decide_depth(self, text: str, intent: dict) -> str:
        t          = text.lower().strip()
        word_count = len(t.split())

        short_signals = [
            "hello", "hi", "hey", "how are you",
            "what time", "what day", "thank you",
            "thanks", "ok", "okay", "yes", "no"
        ]
        if any(s in t for s in short_signals) or word_count <= 4:
            return "short"

        deep_signals = [
            "explain", "research", "tell me everything",
            "in detail", "comprehensive", "deep dive",
            "compare", "difference between", "how does",
            "make a plan", "roadmap", "step by step",
            "write code", "write program", "write function"
        ]
        if any(s in t for s in deep_signals) or word_count > 15:
            return "deep"

        return "medium"


    # ─────────────────────────────────────────────
    # STEP 4 — DECIDE RESPONSE STYLE
    # ─────────────────────────────────────────────

    def _decide_style(self, text: str, intent: dict, reasoning: list) -> str:
        t = text.lower()

        q_type = "general"
        for step in reasoning:
            if isinstance(step, str) and "Question type:" in step:
                q_type = step.split("Question type:")[-1].strip().lower()
                break

        if q_type in ("conversational", "memory_query"):
            return "conversational"
        if q_type in ("procedural", "comparative", "definitional"):
            return "structured"
        if q_type in ("advisory", "causal"):
            return "direct"

        if any(w in t for w in ["list", "steps", "how to", "explain"]):
            return "structured"
        if any(w in t for w in ["should", "recommend", "better", "best"]):
            return "direct"

        return "conversational"


    # ─────────────────────────────────────────────
    # STEP 5 — DECIDE PRIORITY ACTION
    # ─────────────────────────────────────────────

    def _decide_priority_action(self, text: str, intent: dict, memories: str) -> str:
        t       = text.lower()
        primary = intent.get("primary", "") if isinstance(intent, dict) else ""

        if any(w in t for w in [
            "what do you know", "remember me", "about me", "my name", "who am i"
        ]):
            return "recall_user_profile"

        if primary == "automation":
            return "execute_automation"

        if any(w in t for w in [
            "what is", "explain", "tell me", "how does", "why does", "what are"
        ]):
            return "provide_information"

        if any(w in t for w in [
            "write", "create", "make", "build", "generate", "code", "function"
        ]):
            return "create_content"

        if any(w in t for w in [
            "plan", "roadmap", "steps", "how to start", "how do i", "guide me", "help me"
        ]):
            return "create_plan"

        if any(w in t for w in ["hello", "hi", "how are", "what's up"]):
            return "casual_conversation"

        return "general_response"


    # ─────────────────────────────────────────────
    # STEP 6 — WEB SEARCH DECISION
    # ─────────────────────────────────────────────

    def _needs_web_search(self, text: str, knowledge: str) -> bool:
        t = text.lower()

        realtime_signals = [
            "latest", "current", "today", "right now",
            "live", "price", "stock", "news", "weather now",
            "recent", "this week", "this month", "2026"
        ]
        if any(s in t for s in realtime_signals):
            return True

        gap_signals = ["i don't know", "not sure about", "find out", "look up", "search for"]
        if any(s in t for s in gap_signals):
            return True

        if knowledge and len(knowledge) > 100:
            return False

        return False


    # ─────────────────────────────────────────────
    # STEP 7 — CALCULATE CONFIDENCE
    # ─────────────────────────────────────────────

    def _calculate_confidence(self, intent: dict, memories: str, knowledge: str) -> float:
        base = intent.get("confidence", 0.7) if isinstance(intent, dict) else 0.7
        if memories  and len(memories)  > 50:  base = min(1.0, base + 0.1)
        if knowledge and len(knowledge) > 100: base = min(1.0, base + 0.1)
        return round(base, 2)


    # ─────────────────────────────────────────────
    # STEP 8 — REASONING HINT
    # ─────────────────────────────────────────────

    def _generate_reasoning_hint(self, text: str, action: str, depth: str, memories: str) -> str:
        hints = {
            "recall_user_profile":  (
                "User is asking about themselves. Use the memory provided. "
                "Speak naturally, not like reading a database."
            ),
            "execute_automation":   "Confirm the action taken briefly. One sentence maximum.",
            "provide_information":  f"Give a {depth} response. Start with the direct answer, then explain.",
            "create_content":       "Create exactly what was asked. Include brief explanation after the content.",
            "create_plan":          "Create a structured, phased plan. Be specific and actionable, not generic.",
            "casual_conversation":  "Keep it warm and brief. 2 sentences maximum. Use the user's name naturally.",
            "general_response":     f"Give a {depth} response. Be direct and useful.",
        }
        hint = hints.get(action, hints["general_response"])
        if memories and len(memories) > 20:
            hint += " Integrate user context naturally if relevant."
        return hint


    # ─────────────────────────────────────────────
    # TRACK DECISIONS
    # ─────────────────────────────────────────────

    def _track_decision(self, user_input: str, decision: dict):
        self.decision_history.append({
            "time":       datetime.now().strftime("%H:%M"),
            "input":      user_input[:80],
            "action":     decision["priority_action"],
            "depth":      decision["response_depth"],
            "confidence": decision["confidence"],
        })
        if len(self.decision_history) > 50:
            self.decision_history = self.decision_history[-50:]


    # ─────────────────────────────────────────────
    # BUILD FINAL PROMPT
    # FIX: reasoning/memories/knowledge None guards
    # ─────────────────────────────────────────────

    def build_smart_prompt(
        self,
        user_input: str,
        decision:   dict,
        context:    str,
        reasoning:  list
    ) -> str:
        """
        Build a clean, focused prompt from decision results.
        FIX: all values safely coerced — None never reaches
        .strip() or "\n".join().
        """
        # Coerce every value before use
        user_input = user_input or ""
        context    = context    or ""
        reasoning  = reasoning  if isinstance(reasoning, list) else []
        decision   = decision   if isinstance(decision, dict)  else dict(_SAFE_DECISION)

        top_memories  = decision.get("top_memories",  "") or ""
        top_knowledge = decision.get("top_knowledge", "") or ""
        hint          = decision.get("reasoning_hint", "Answer helpfully.") or "Answer helpfully."
        style         = decision.get("response_style", "conversational")    or "conversational"

        style_instructions = {
            "conversational": "Respond conversationally and warmly.",
            "structured":     "Use clear structure with numbered points or sections.",
            "direct":         "Be direct. Give the answer first, explanation second.",
        }

        parts = []

        if reasoning:
            parts.append(f"Reasoning analysis:\n{chr(10).join(str(s) for s in reasoning)}")

        if top_memories.strip():
            parts.append(f"Relevant user context:\n{top_memories}")

        if top_knowledge.strip():
            parts.append(f"Relevant knowledge:\n{top_knowledge}")

        if context.strip():
            parts.append(f"Conversation context:\n{context}")

        parts.append(f"Response guidance:\n{hint}")
        parts.append(style_instructions.get(style, ""))
        parts.append(f"User: {user_input}\n\nRespond now.")

        return "\n\n".join(p for p in parts if p.strip())
