# ==================================================
# reasoning_engine.py — Vivie Deep Reasoning Engine
# Thinks in 6 layers before every response.
# Silent — shows in terminal only, never spoken.
# ==================================================


class ReasoningEngine:

    def think(
        self,
        user_input: str,
        intent:     dict,
        memory:     str,
        knowledge:  str
    ) -> list:
        """
        Deep 6-layer reasoning before every response.
        Returns list of reasoning steps for terminal + prompt injection.
        """

        steps = []

        # ─────────────────────────────────────────
        # LAYER 1 — QUESTION ANALYSIS
        # ─────────────────────────────────────────
        q_type     = self._classify_question(user_input)
        complexity = self._measure_complexity(user_input)
        steps.append(f"[L1] Question type: {q_type}")
        steps.append(f"[L1] Complexity: {complexity}")

        # ─────────────────────────────────────────
        # LAYER 2 — INTENT UNDERSTANDING
        # ─────────────────────────────────────────
        primary = intent.get("primary", "general") if isinstance(intent, dict) else str(intent)
        goal    = self._extract_goal(user_input, primary)
        steps.append(f"[L2] User goal: {goal}")

        # ─────────────────────────────────────────
        # LAYER 3 — CONTEXT ASSESSMENT
        # ─────────────────────────────────────────
        if memory and memory.strip():
            memory_relevance = self._check_relevance(user_input, memory)
            steps.append(f"[L3] Memory relevance: {memory_relevance}")
        else:
            steps.append("[L3] Memory: none available")

        if knowledge and knowledge.strip():
            knowledge_relevance = self._check_relevance(user_input, knowledge)
            steps.append(f"[L3] Knowledge relevance: {knowledge_relevance}")
        else:
            steps.append("[L3] Knowledge: none available")

        # ─────────────────────────────────────────
        # LAYER 4 — GAP DETECTION
        # ─────────────────────────────────────────
        gaps = self._detect_gaps(user_input, memory, knowledge)
        if gaps:
            steps.append(f"[L4] Gaps detected: {', '.join(gaps)}")
        else:
            steps.append("[L4] No critical gaps — sufficient context")

        # ─────────────────────────────────────────
        # LAYER 5 — RESPONSE STRATEGY
        # ─────────────────────────────────────────
        strategy = self._decide_strategy(q_type, complexity, gaps)
        steps.append(f"[L5] Response strategy: {strategy}")

        # ─────────────────────────────────────────
        # LAYER 6 — QUALITY CHECKLIST
        # ─────────────────────────────────────────
        checklist = self._build_checklist(q_type, goal, memory, knowledge)
        for item in checklist:
            steps.append(f"[L6] Must include: {item}")

        return steps


    # ─────────────────────────────────────────────
    # LAYER 1 — QUESTION CLASSIFIER
    # ─────────────────────────────────────────────

    def _classify_question(self, text: str) -> str:
        t = text.lower().strip()

        if any(w in t for w in ["what is", "what are", "define", "explain"]):
            return "definitional"

        elif any(w in t for w in ["how do", "how to", "how can", "steps to"]):
            return "procedural"

        elif any(w in t for w in ["why", "reason", "cause", "because"]):
            return "causal"

        elif any(w in t for w in ["who is", "tell me about", "biography"]):
            return "biographical"

        elif any(w in t for w in ["when", "what time", "what date", "how long"]):
            return "temporal"

        elif any(w in t for w in ["where", "location", "place", "city"]):
            return "locational"

        elif any(w in t for w in ["compare", "difference", "better", "vs", "versus"]):
            return "comparative"

        elif any(w in t for w in ["should i", "what do you think", "opinion", "recommend"]):
            return "advisory"

        elif any(w in t for w in ["hello", "hi", "hey", "how are you", "how r u"]):
            return "conversational"

        elif any(w in t for w in ["remember", "recall", "what do you know", "tell me about me"]):
            return "memory_query"

        elif any(w in t for w in ["calculate", "how much", "how many", "count"]):
            return "computational"

        else:
            return "general"


    def _measure_complexity(self, text: str) -> str:
        word_count             = len(text.split())
        has_multiple_questions = text.count("?") > 1
        has_technical_terms    = any(w in text.lower() for w in [
            "algorithm", "neural", "machine learning", "architecture",
            "database", "api", "system", "pipeline", "model", "code",
            "deep learning", "transformer", "embedding", "vector"
        ])

        if word_count <= 4:
            return "simple"
        elif has_multiple_questions or has_technical_terms or word_count > 20:
            return "complex"
        else:
            return "moderate"


    # ─────────────────────────────────────────────
    # LAYER 2 — GOAL EXTRACTOR (FIXED)
    # ─────────────────────────────────────────────

    def _extract_goal(self, text: str, intent: str) -> str:
        t = text.lower()

        # ✅ Check content FIRST — more accurate than intent label
        if any(w in t for w in ["explain", "difference", "compare", "vs", "versus"]):
            return "analytical query — explain clearly with structure"

        if any(w in t for w in ["how to", "how do", "steps", "guide"]):
            return "procedural query — give step by step answer"

        if any(w in t for w in ["what is", "what are", "define", "meaning of"]):
            return "definitional query — explain clearly and concisely"

        if any(w in t for w in ["why", "reason", "cause"]):
            return "causal query — explain cause and effect"

        if any(w in t for w in ["should i", "recommend", "suggest", "opinion"]):
            return "advisory query — give clear recommendation"

        if any(w in t for w in ["calculate", "how much", "how many"]):
            return "computational query — calculate and show steps"

        # Then check intent for remaining cases
        if intent == "chat":
            if any(w in t for w in ["hello", "hi", "hey", "how are", "how r"]):
                return "social greeting — respond warmly and briefly"

            elif any(w in t for w in ["about you", "who are you", "what are you"]):
                return "identity query — describe capabilities confidently"

            elif any(w in t for w in ["what do you know", "remember", "recall", "about me"]):
                return "memory retrieval — summarize known user info naturally"

            else:
                return "general conversation — engage naturally and helpfully"

        elif intent == "automation":
            return "execute system action — confirm and proceed"

        elif intent == "question":
            return "provide accurate factual answer"

        else:
            return f"fulfill {intent} request clearly and precisely"


    # ─────────────────────────────────────────────
    # LAYER 3 — RELEVANCE CHECKER
    # ─────────────────────────────────────────────

    def _check_relevance(self, query: str, context: str) -> str:
        if not context or not context.strip():
            return "none"

        query_words   = set(query.lower().split())
        context_words = set(context.lower().split())
        overlap       = len(query_words & context_words)

        if overlap >= 4:
            return "high"
        elif overlap >= 2:
            return "medium"
        else:
            return "low"


    # ─────────────────────────────────────────────
    # LAYER 4 — GAP DETECTOR
    # ─────────────────────────────────────────────

    def _detect_gaps(self, text: str, memory: str, knowledge: str) -> list:
        gaps = []
        t    = text.lower()

        if any(w in t for w in ["current", "latest", "today", "now", "live", "price", "news"]):
            gaps.append("requires real-time data")

        if any(w in t for w in ["my", "i am", "about me", "you know me"]) and not memory:
            gaps.append("user context missing")

        if any(w in t for w in [
            "code", "python", "algorithm", "ai", "model",
            "system", "deep learning", "machine learning"
        ]) and not knowledge:
            gaps.append("technical knowledge not in database yet")

        if any(w in t for w in ["will", "future", "predict", "forecast", "going to"]):
            gaps.append("future prediction — state uncertainty clearly")

        if any(w in t for w in ["personal", "private", "secret", "confidential"]):
            gaps.append("sensitive topic — respond carefully")

        return gaps


    # ─────────────────────────────────────────────
    # LAYER 5 — STRATEGY DECIDER
    # ─────────────────────────────────────────────

    def _decide_strategy(self, q_type: str, complexity: str, gaps: list) -> str:

        if q_type == "conversational":
            return "short warm reply — no structure needed"

        elif q_type == "procedural":
            return "numbered steps — clear and sequential"

        elif q_type == "comparative":
            return "side by side comparison — highlight key differences"

        elif q_type == "causal":
            return "explain cause and effect chain clearly"

        elif q_type == "advisory":
            return "give recommendation first — brief justification after"

        elif q_type == "memory_query":
            return "retrieve and summarize user profile naturally"

        elif q_type == "computational":
            return "calculate step by step — show working clearly"

        elif q_type == "biographical":
            return "structured profile — key facts first"

        elif q_type == "definitional" and complexity == "complex":
            return "structured explanation — definition then examples"

        elif q_type == "definitional" and complexity == "simple":
            return "one clear sentence definition"

        elif "requires real-time data" in gaps:
            return "use web search data — summarize and cite sources"

        elif "future prediction" in gaps:
            return "give best estimate — clearly state it is not certain"

        else:
            return "clear direct answer — concise and precise"


    # ─────────────────────────────────────────────
    # LAYER 6 — QUALITY CHECKLIST
    # ─────────────────────────────────────────────

    def _build_checklist(
        self,
        q_type:    str,
        goal:      str,
        memory:    str,
        knowledge: str
    ) -> list:

        checklist = []

        # Always required
        checklist.append("answer the actual question directly")
        checklist.append("do not repeat the user's question")
        checklist.append("do not say 'As an AI'")

        # Based on question type
        if q_type == "conversational":
            checklist.append("keep response under 2 sentences")
            checklist.append("warm but not overly emotional")

        elif q_type == "procedural":
            checklist.append("number each step clearly")
            checklist.append("confirm completion at end")

        elif q_type == "memory_query":
            checklist.append("use stored memory naturally")
            checklist.append("do not list raw data — speak conversationally")

        elif q_type == "advisory":
            checklist.append("give a clear recommendation first")
            checklist.append("briefly justify the recommendation")

        elif q_type == "comparative":
            checklist.append("address both sides fairly")
            checklist.append("give final verdict if possible")

        elif q_type == "causal":
            checklist.append("identify root cause clearly")
            checklist.append("explain downstream effects")

        elif q_type == "computational":
            checklist.append("show calculation steps")
            checklist.append("state final answer clearly")

        elif q_type == "definitional":
            checklist.append("start with clear definition")
            checklist.append("add example if helpful")

        # Context based
        if memory and memory.strip():
            checklist.append("reference user context naturally if relevant")

        if knowledge and knowledge.strip():
            checklist.append("integrate knowledge base data into answer")

        return checklist