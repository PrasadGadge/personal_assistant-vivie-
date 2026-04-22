# ==================================================
# auto_learning_engine.py — Vivie Self Learning
# Every night at 12 AM Vivie analyzes her own
# conversations, finds gaps, and teaches herself.
# ==================================================

import threading
import time
import datetime
import os
import json
import re

from Brain.cl_brain              import Main_Brain
from Features.web_search         import search_web
from knowledge_core.chroma_manager import get_chroma_manager
from memory_core.episodic_memory import _load_episodes

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR   = os.path.dirname(BASE_DIR)
LEARNING_LOG  = os.path.join(PROJECT_DIR, "data", "learning_log.json")

LEARN_HOUR    = 0   # 12 AM
LEARN_MINUTE  = 0


# ─────────────────────────────────────────────────
# LOAD / SAVE LEARNING LOG
# ─────────────────────────────────────────────────

def _load_log() -> dict:
    if not os.path.exists(LEARNING_LOG):
        return {"sessions": [], "total_learned": 0}
    try:
        with open(LEARNING_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": [], "total_learned": 0}


def _save_log(log: dict):
    try:
        os.makedirs(os.path.dirname(LEARNING_LOG), exist_ok=True)
        with open(LEARNING_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[AutoLearning] Log save error: {e}")


# ─────────────────────────────────────────────────
# CLEAN LLM OUTPUT
# Strips JSON/markdown so text can be stored cleanly
# ─────────────────────────────────────────────────

def _clean_llm_output(text: str) -> str:
    """
    Strip JSON formatting, markdown code blocks,
    and convert JSON dicts to readable plain text.
    """
    if not text:
        return ""

    # Remove markdown code blocks
    text = re.sub(r'```json', '', text)
    text = re.sub(r'```',     '', text)
    text = text.strip()

    # If JSON dict — flatten to readable text
    if text.startswith('{'):
        try:
            parsed = json.loads(text)
            flat   = ""
            for key, value in parsed.items():
                if isinstance(value, str):
                    flat += f"{key}: {value}\n"
                elif isinstance(value, list):
                    flat += f"{key}:\n"
                    for item in value:
                        flat += f"  - {item}\n"
                elif isinstance(value, dict):
                    flat += f"{key}:\n"
                    for k, v in value.items():
                        flat += f"  {k}: {v}\n"
            return flat.strip()
        except Exception:
            pass

    return text.strip()


# ─────────────────────────────────────────────────
# STEP 1 — ANALYZE PAST CONVERSATIONS
# Find what Vivie didn't know or got wrong
# ─────────────────────────────────────────────────

def _analyze_conversations() -> list:
    """
    Analyze today's episodes to find:
    - Topics Vivie lacked knowledge on
    - Questions she couldn't answer well
    - Gaps detected in reasoning
    """
    try:
        episodes  = _load_episodes()
        if not episodes:
            print("[AutoLearning] No episodes to analyze.")
            return []

        # Get today's episodes only
        today     = datetime.date.today().isoformat()
        today_eps = [
            ep for ep in episodes
            if ep.get("date") == today
        ]

        if not today_eps:
            # Fall back to last 10 episodes
            today_eps = episodes[-10:]

        if not today_eps:
            return []

        # Build conversation summary
        convo_summary = ""
        for ep in today_eps[-15:]:
            convo_summary += (
                f"User asked: {ep.get('user_input', '')}\n"
                f"Vivie answered: {ep.get('vivie_response', '')[:150]}\n"
                f"Intent: {ep.get('intent', '')}\n\n"
            )

        # Ask LLM to identify knowledge gaps
        analysis_prompt = f"""Analyze these conversations and identify topics where knowledge was lacking.

Conversations:
{convo_summary}

Return ONLY a valid JSON array like this exact format:
[
  {{"topic": "topic name here", "reason": "why vivie needs to learn this"}},
  {{"topic": "another topic", "reason": "reason here"}}
]

Maximum 5 topics. Return ONLY the JSON array, no other text."""

        response = Main_Brain(analysis_prompt)

        # Clean and parse
        response = _clean_llm_output(response)

        # Extract JSON array
        json_match = re.search(r'\[.*?\]', response, re.DOTALL)
        if not json_match:
            print("[AutoLearning] Could not parse topics from LLM response.")
            return []

        topics = json.loads(json_match.group())
        print(f"[AutoLearning] Found {len(topics)} topics to learn.")
        return topics

    except Exception as e:
        print(f"[AutoLearning] Analysis error: {e}")
        return []


# ─────────────────────────────────────────────────
# STEP 2 — SELF EVALUATE PERFORMANCE
# Rate today's responses
# ─────────────────────────────────────────────────

def _self_evaluate() -> dict:
    """
    Vivie evaluates her own performance today.
    Returns evaluation summary.
    """
    try:
        episodes  = _load_episodes()
        today     = datetime.date.today().isoformat()
        today_eps = [ep for ep in episodes if ep.get("date") == today]

        if not today_eps:
            today_eps = episodes[-5:]

        if not today_eps:
            return {}

        total    = len(today_eps)
        positive = sum(1 for ep in today_eps if ep.get("reaction") == "positive")
        negative = sum(1 for ep in today_eps if ep.get("reaction") == "negative")

        topics = list(set([
            ep.get("topic", "general")
            for ep in today_eps
        ]))

        evaluation = {
            "date":            today,
            "total_responses": total,
            "positive":        positive,
            "negative":        negative,
            "neutral":         total - positive - negative,
            "satisfaction":    round((positive / total * 100) if total > 0 else 0, 1),
            "topics_covered":  topics[:10]
        }

        print(f"[AutoLearning] Self evaluation: {positive}/{total} positive responses")
        return evaluation

    except Exception as e:
        print(f"[AutoLearning] Evaluation error: {e}")
        return {}


# ─────────────────────────────────────────────────
# STEP 3 — DEEP LEARN A TOPIC
# Search + synthesize + store in ChromaDB
# ─────────────────────────────────────────────────

def _learn_topic(topic: str, reason: str) -> bool:
    """
    Learn a single topic deeply:
    1. Search web for latest info
    2. Synthesize into clean knowledge
    3. Store directly in ChromaDB bypassing importance filter
    """
    try:
        print(f"[AutoLearning] Learning: '{topic}'")

        # Search multiple angles
        results_1 = search_web(topic)
        results_2 = search_web(f"{topic} explained simply")

        all_content = ""
        for results in [results_1, results_2]:
            if results:
                for r in results[:2]:
                    title   = r.get("title", "")
                    content = r.get("content", "") or r.get("snippet", "")
                    if content:
                        all_content += f"{title}: {content}\n\n"

        # Synthesize with LLM
        synthesis_prompt = f"""Create a clear knowledge entry about this topic.

Topic: {topic}
Reason to learn: {reason}
Web sources: {all_content[:2000] if all_content else "Use your knowledge"}

Write in plain text format:
TOPIC: {topic}
SUMMARY: 2-3 sentence summary
KEY FACTS:
- fact 1
- fact 2
- fact 3
PRACTICAL USE: how this applies to AI or coding

Use plain text only. No JSON. No markdown code blocks."""

        knowledge = Main_Brain(synthesis_prompt)

        if not knowledge or len(knowledge) < 50:
            print(f"[AutoLearning] Insufficient knowledge generated for: '{topic}'")
            return False

        # Clean output
        knowledge = _clean_llm_output(knowledge)

        if len(knowledge) < 50:
            print(f"[AutoLearning] Knowledge too short after cleaning: '{topic}'")
            return False

        # ✅ Store directly in ChromaDB — bypass importance filter
        # Auto-learning content is always important
        chroma = get_chroma_manager()
        stored = chroma.store(
            knowledge,
            {
                "source":     "auto_learning",
                "topic":      topic,
                "reason":     reason,
                "learned_at": datetime.datetime.now().isoformat(),
                "importance": "5"
            }
        )

        if stored:
            print(f"[AutoLearning] ✅ Stored: '{topic}'")
            return True
        else:
            print(f"[AutoLearning] Already exists: '{topic}'")
            return False

    except Exception as e:
        print(f"[AutoLearning] Learn topic error: {e}")
        return False


# ─────────────────────────────────────────────────
# STEP 4 — GENERATE IMPROVEMENT INSIGHTS
# What should Vivie do better tomorrow
# ─────────────────────────────────────────────────

def _generate_improvement_plan(evaluation: dict, topics_learned: list) -> str:
    """
    Generate what Vivie should improve tomorrow.
    """
    try:
        if not evaluation:
            return ""

        prompt = f"""Based on Vivie's performance today:

Total responses: {evaluation.get('total_responses', 0)}
Positive reactions: {evaluation.get('positive', 0)}
Negative reactions: {evaluation.get('negative', 0)}
Satisfaction rate: {evaluation.get('satisfaction', 0)}%
Topics covered today: {evaluation.get('topics_covered', [])}
New topics learned tonight: {[t.get('topic','') for t in topics_learned]}

Write 3 specific improvements Vivie should focus on tomorrow.
Plain text only. Format:
1. improvement one
2. improvement two
3. improvement three"""

        response = Main_Brain(prompt)
        return _clean_llm_output(response)

    except Exception as e:
        print(f"[AutoLearning] Improvement plan error: {e}")
        return ""


# ─────────────────────────────────────────────────
# MAIN LEARNING SESSION
# ─────────────────────────────────────────────────

def run_learning_session():
    """
    Full nightly learning session:
    1. Analyze today's conversations
    2. Self evaluate performance
    3. Learn identified topics
    4. Generate improvement plan
    5. Log everything
    """
    print("\n" + "="*50)
    print("[AutoLearning] 🧠 Nightly learning session starting...")
    print("="*50)

    session_start = datetime.datetime.now().isoformat()
    learned_count = 0

    # Step 1 — Analyze conversations
    print("[AutoLearning] Step 1: Analyzing today's conversations...")
    topics_to_learn = _analyze_conversations()

    # Step 2 — Self evaluate
    print("[AutoLearning] Step 2: Self evaluation...")
    evaluation = _self_evaluate()

    # Step 3 — Learn each topic
    print(f"[AutoLearning] Step 3: Learning {len(topics_to_learn)} new topics...")
    for topic_data in topics_to_learn:
        topic  = topic_data.get("topic", "")
        reason = topic_data.get("reason", "")
        if topic:
            if _learn_topic(topic, reason):
                learned_count += 1
            time.sleep(2)  # Avoid API rate limits

    # Step 4 — Improvement plan
    print("[AutoLearning] Step 4: Generating improvement plan...")
    improvements = _generate_improvement_plan(evaluation, topics_to_learn)

    if improvements:
        print(f"[AutoLearning] Tomorrow's improvements:\n{improvements}")

    # Step 5 — Save to log
    log = _load_log()
    session = {
        "date":            datetime.date.today().isoformat(),
        "session_start":   session_start,
        "session_end":     datetime.datetime.now().isoformat(),
        "topics_analyzed": len(topics_to_learn),
        "topics_learned":  learned_count,
        "evaluation":      evaluation,
        "improvements":    improvements,
        "topics":          topics_to_learn
    }

    log["sessions"].append(session)
    log["total_learned"] += learned_count
    _save_log(log)

    print(f"\n[AutoLearning] ✅ Session complete.")
    print(f"[AutoLearning] Topics learned tonight: {learned_count}/{len(topics_to_learn)}")
    print(f"[AutoLearning] Total lifetime knowledge: {log['total_learned']}")
    print("="*50 + "\n")


# ─────────────────────────────────────────────────
# BACKGROUND SCHEDULER
# Waits for 12 AM and runs session
# ─────────────────────────────────────────────────

def _learning_scheduler():
    """Waits for 12 AM and runs nightly learning."""
    print("[AutoLearning] Scheduler active — will learn at 12 AM.")

    last_run_date = None

    while True:
        try:
            now = datetime.datetime.now()

            if (now.hour   == LEARN_HOUR   and
                now.minute == LEARN_MINUTE and
                last_run_date != now.date()):

                last_run_date = now.date()
                run_learning_session()

        except Exception as e:
            print(f"[AutoLearning] Scheduler error: {e}")

        time.sleep(30)


# ─────────────────────────────────────────────────
# START
# ─────────────────────────────────────────────────

def start_auto_learning():
    """Launch auto learning in background thread."""
    t = threading.Thread(target=_learning_scheduler, daemon=True)
    t.start()
    print("[AutoLearning] Engine started — learning at 12 AM nightly.")