# ==========================================
# SYSTEM LLM (Isolated Brain)
# Used for intent detection, memory classification, etc.
# ==========================================

from Brain.api_brain import api_generate_response


def system_llm(prompt: str) -> str:
    """
    Pure LLM call.
    No personality.
    No conversation history.
    No saving.
    No dynamic prompt.
    """

    try:
        response = api_generate_response(prompt)
        return response.strip()

    except Exception as e:
        print(f"[System LLM Error]: {e}")
        return ""