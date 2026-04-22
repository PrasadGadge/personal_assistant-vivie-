"""
rag_retrieve.py — Vivie's Smart Knowledge Retrieval
Now powered by ChromaDB semantic search.
"""

from knowledge_core.chroma_manager import get_chroma_manager
import logging

logger = logging.getLogger("RAGRetrieve")


def retrieve_knowledge(query: str, top_k: int = 3, threshold: float = 0.4) -> str:
    """
    Retrieve relevant knowledge for a query.
    Returns formatted string ready to inject into LLM prompt.
    """
    try:
        chroma = get_chroma_manager()
        results = chroma.retrieve(query, top_k=top_k, threshold=threshold)

        if not results:
            return ""

        # Format for LLM prompt injection
        formatted = "\n".join([f"- {r}" for r in results])
        return f"[Relevant Knowledge]\n{formatted}"

    except Exception as e:
        logger.error(f"[RAGRetrieve] Failed: {e}")
        return ""


def retrieve_knowledge_detailed(query: str, top_k: int = 3) -> list:
    """
    Returns detailed results with similarity scores.
    Useful for debugging or advanced use.
    """
    try:
        chroma = get_chroma_manager()
        return chroma.retrieve_with_metadata(query, top_k=top_k)
    except Exception as e:
        logger.error(f"[RAGRetrieve Detailed] Failed: {e}")
        return []