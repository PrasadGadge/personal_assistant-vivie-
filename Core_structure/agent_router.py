# ==================================================
# agent_router.py — Vivie Multi-Agent Router
# Fixed: language detection, uncaught exceptions,
#        error strings reaching TTS, None returns,
#        comparison extraction garbage
# ==================================================

from Brain.cl_brain import Main_Brain
from Features.web_search import search_web


# ─────────────────────────────────────────────────
# SAFE LLM WRAPPER
# All agent calls go through here.
# Guarantees a string back — never None, never raises.
# ─────────────────────────────────────────────────

def _safe_llm(prompt: str, fallback: str = "") -> str:
    """
    Call Main_Brain and guarantee a non-None string.
    Prevents error strings from leaking into TTS output.
    """
    try:
        result = Main_Brain(prompt)
        # Main_Brain can return None on LLM timeout/error
        if not result or not str(result).strip():
            return fallback or "I ran into an issue processing that. Please try again."
        return str(result).strip()
    except Exception as e:
        print(f"[LLM] Error: {e}")
        return fallback or "I ran into an issue processing that. Please try again."


# ─────────────────────────────────────────────────
# AGENT DETECTOR
# ─────────────────────────────────────────────────

def detect_agent(text: str) -> str:
    """
    Detect which agent should handle input.
    Returns: "research" | "code" | "planning" | "none"

    Order matters: more specific triggers checked first.
    """
    t = text.lower().strip()

    # ── Code Agent ────────────────────────────────
    code_triggers = [
        "write code", "write a code", "create code",
        "write program", "write a program",
        "write function", "write a function",
        "write script", "write a script",
        "code for", "program for",
        "how to code", "explain code",
        "debug", "fix code", "fix this code",
        "what does this code", "explain this code",
        "write in python", "write in c++",
        "write in javascript", "write in java",
        "implement", "make a function",
        "create a function", "build a function"
    ]
    if any(trigger in t for trigger in code_triggers):
        return "code"

    # ── Research Agent ────────────────────────────
    research_triggers = [
        "research", "deep research", "find out",
        "search about", "look up", "investigate",
        "tell me everything about", "full information",
        "detailed information", "give me details about",
        "what is the latest on", "find information",
        "gather information", "study about",
        "tell me all about", "comprehensive",
        "in depth", "detailed report",
        "everything about", "full report on",
        "compare", "vs", "versus",
        "difference between", "knowledge map",
        "research history", "what have you researched"
    ]
    if any(trigger in t for trigger in research_triggers):
        return "research"

    # ── Planning Agent ────────────────────────────
    planning_triggers = [
        "make a plan", "create a plan", "plan for",
        "plan to", "how should i", "help me plan",
        "break down", "break this down", "steps to",
        "roadmap", "strategy", "how to achieve",
        "how to reach", "guide me", "walk me through",
        "step by step plan", "what steps",
        "how do i start", "where do i start",
        "help me build", "help me create",
        "schedule for", "timeline for"
    ]
    if any(trigger in t for trigger in planning_triggers):
        return "planning"

    return "none"


# ─────────────────────────────────────────────────
# LANGUAGE DETECTOR
# FIX: "java" was matching inside "javascript"
# ─────────────────────────────────────────────────

def _detect_language(text: str) -> str:
    """
    Detect preferred programming language from text.
    Checks javascript BEFORE java so 'java' doesn't
    match inside 'javascript'.
    c++ uses literal match since \b fails on + chars.
    """
    import re
    t = text.lower()

    if re.search(r'\bjavascript\b|\bjs\b|\bnode\b|\breact\b', t):
        return "JavaScript"
    if 'c++' in t or 'cpp' in t or 'c plus plus' in t:
        return "C++"
    if re.search(r'\bpython\b|\bdjango\b|\bflask\b', t):
        return "Python"
    if re.search(r'\bjava\b|\bspring\b', t):
        return "Java"
    if re.search(r'\bhtml\b|\bcss\b|web page', t):
        return "HTML/CSS"
    return "Python"


# ─────────────────────────────────────────────────
# RESEARCH AGENT
# ─────────────────────────────────────────────────

def research_agent(query: str) -> str:
    """
    Deep research agent powered by ResearchEngine.
    Falls back gracefully if engine is unavailable.
    Always returns a non-empty string.
    """
    print(f"[ResearchAgent] Activated for: '{query[:50]}'")

    try:
        from Core_structure.research_engine import get_research_engine
        engine = get_research_engine()
        t      = query.lower().strip()

        # ── Knowledge map / history query ─────────
        if any(w in t for w in [
            "knowledge map", "what have you researched",
            "research history", "past research",
            "previous research", "show knowledge graph"
        ]):
            if any(w in t for w in ["history", "previous", "past"]):
                return engine.get_research_history() or "No research history yet."
            topic = None
            for prep in ["about", "for", "on"]:
                pattern = rf'\b{prep}\s+(.+)'
                import re
                m = re.search(pattern, t)
                if m:
                    topic = m.group(1).strip()
                    break
            return engine.get_knowledge_map(topic) or "No knowledge map available."

        # ── Comparison query ──────────────────────
        # FIX: was injecting "|" into text then splitting on it,
        # producing garbage when query already contained "|"
        compare_words = ["vs", "versus", "compare between",
                         "compare", "difference between"]
        matched_word = None
        for w in compare_words:
            if w in t:
                matched_word = w
                break

        if matched_word:
            # Split on the comparison word only once
            parts = t.split(matched_word, 1)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) == 2:
                # Clean up common filler words
                for filler in ["what is the", "what are", "tell me about",
                               "explain", "the difference between"]:
                    parts[0] = parts[0].replace(filler, "").strip()
                    parts[1] = parts[1].replace(filler, "").strip()
                if parts[0] and parts[1]:
                    return engine.compare_topics(parts[0], parts[1])

        # ── Deep research ─────────────────────────
        result = engine.deep_research(query, depth=3)
        return result or _research_fallback(query)

    except Exception as e:
        print(f"[ResearchAgent] Engine unavailable: {e} — using fallback")
        return _research_fallback(query)


def _research_fallback(query: str) -> str:
    """
    Web-search fallback when ResearchEngine is unavailable.
    FIX: final LLM call now goes through _safe_llm so
    it can never return None.
    """
    print(f"[ResearchAgent] Running fallback for: '{query[:50]}'")
    try:
        results_1 = search_web(query)
        results_2 = search_web(f"{query} latest 2026")
        results_3 = search_web(f"{query} explained")

        all_content = ""
        for results in [results_1, results_2, results_3]:
            if results:
                for r in results[:2]:
                    title   = r.get("title", "")
                    content = r.get("content", "") or r.get("snippet", "")
                    if title or content:
                        all_content += f"Source: {title}\n{content}\n\n"

        if not all_content:
            # No web data — go straight to LLM knowledge
            raise ValueError("No web content found")

        prompt = f"""You are Vivie's Research Agent.

Research Query: {query}

Web Sources:
{all_content[:3000]}

Provide a comprehensive, structured research report:
1. Key findings
2. Recent developments
3. Important insights
4. Connections to related topics"""

        return _safe_llm(prompt)

    except Exception as e:
        print(f"[ResearchAgent] Fallback web search failed: {e} — using LLM only")
        prompt = (
            f"Research this topic thoroughly: {query}\n"
            f"Provide overview, key facts, recent developments, and insights."
        )
        return _safe_llm(prompt)


# ─────────────────────────────────────────────────
# CODE AGENT
# ─────────────────────────────────────────────────

def code_agent(query: str) -> str:
    """
    Code specialist — writes clean production-quality code.
    FIX: errors no longer return strings that get spoken aloud.
    """
    print(f"[CodeAgent] Activated for: '{query[:50]}'")

    language = _detect_language(query)

    prompt = f"""You are Vivie's Code Agent — a specialist software engineer.

User Request: {query}
Preferred Language: {language}

Your task:
1. Write clean, working code
2. Add clear comments explaining each part
3. Show example usage
4. Explain what the code does in 2-3 sentences
5. Mention any important notes or edge cases

Format:
[CODE]
<the actual code>
[EXPLANATION]
<brief explanation>
[USAGE]
<example usage>

Write production-quality code."""

    return _safe_llm(
        prompt,
        fallback="I had trouble generating the code. Please try rephrasing your request."
    )


# ─────────────────────────────────────────────────
# PLANNING AGENT
# ─────────────────────────────────────────────────

def planning_agent(query: str, memory_block: str = "") -> str:
    """
    Planning specialist — creates actionable roadmaps.
    FIX: errors no longer return strings that get spoken aloud.
    """
    print(f"[PlanningAgent] Activated for: '{query[:50]}'")

    user_context = ""
    if memory_block and memory_block.strip():
        user_context = f"\nUser context from memory: {memory_block[:300]}"

    prompt = f"""You are Vivie's Planning Agent — a specialist in strategic planning.

Planning Request: {query}
{user_context}

Your task:
1. Break this goal into clear phases
2. Add specific actionable steps per phase
3. Add realistic time estimates
4. Highlight what to prioritize first
5. Mention potential challenges

Format:
GOAL: <restate goal>

PHASE 1 — <name> (<time estimate>)
- Step 1
- Step 2

PHASE 2 — <name> (<time estimate>)
- Step 1

PRIORITY: <what to focus on first>
CHALLENGES: <key challenges>

Make it specific, realistic and immediately actionable."""

    return _safe_llm(
        prompt,
        fallback="I had trouble creating a plan. Please try rephrasing your request."
    )


# ─────────────────────────────────────────────────
# MAIN ROUTER
# FIX: wrapped in try/except so exceptions from any
# agent function never propagate up to main_brain.py
# ─────────────────────────────────────────────────

def route_to_agent(
    text:         str,
    memory_block: str = "",
    knowledge:    str = ""
) -> tuple:
    """
    Detect agent type and route automatically.
    Returns: (agent_name, response_string)
    ALWAYS returns a tuple — never raises.
    """
    try:
        agent_type = detect_agent(text)

        if agent_type == "none":
            return ("none", "")

        print(f"[AgentRouter] Routing to: {agent_type.upper()} agent")

        if agent_type == "research":
            return ("research", research_agent(text))

        if agent_type == "code":
            return ("code", code_agent(text))

        if agent_type == "planning":
            return ("planning", planning_agent(text, memory_block))

        # Unknown type — shouldn't happen but guard anyway
        return ("none", "")

    except Exception as e:
        # Last-resort catch — log it, return safe fallback
        print(f"[AgentRouter] Unexpected error routing '{text[:50]}': {e}")
        return ("none", "")
