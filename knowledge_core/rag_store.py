"""
rag_store.py — Vivie's Knowledge Storage
Now stores into ChromaDB with semantic indexing.
"""

from knowledge_core.chroma_manager import get_chroma_manager
import logging

logger = logging.getLogger("RAGStore")

def calculate_importance(text: str) -> int:
    score = 0
    t = text.lower()

    personal = ["my name", "i am", "i live", "i like", 
                "i work", "i study", "i prefer", "i love"]
    if any(p in t for p in personal):
        score += 3

    if "important" in t or "remember" in t:
        score += 2

    if len(text.split()) > 15:
        score += 1

    casual = ["hello", "hi", "okay", "thanks", 
              "bye", "good", "great", "nice"]
    if any(c in t for c in casual):
        score -= 2

    return max(0, score)


def store_knowledge(text: str, metadata: dict = None) -> bool:
    try:
        # ✅ Only store if important enough
        score = calculate_importance(text)
        if score < 1:
            print(f"[RAGStore] Skipped low importance (score={score}): '{text[:40]}'")
            return False

        if metadata is None:
            metadata = {}
        metadata["importance"] = score  # ← save score with entry

        chroma = get_chroma_manager()
        return chroma.store(text, metadata)

    except Exception as e:
        logger.error(f"[RAGStore] Failed: {e}")
        return False


def store_conversation_knowledge(user_input: str, vivie_response: str) -> bool:
    """
    Automatically extract + store knowledge from conversations.
    Call this at end of every conversation turn.
    """
    try:
        chroma = get_chroma_manager()
        text   = f"User asked: {user_input} | Vivie answered: {vivie_response}"
        meta   = {
            "type":       "conversation",
            "user_input": user_input[:100]
        }
        return chroma.store(text, meta)
    except Exception as e:
        logger.error(f"[RAGStore Conversation] Failed: {e}")
        return False