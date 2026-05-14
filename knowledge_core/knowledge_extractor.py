def extract_knowledge(user_input, response, source: str = "llm"):
    """
    Extract lightweight knowledge from non-LLM sources.
    Use source="tool"/"agent" to enable extraction, or "llm" to skip.
    """

    if source == "llm":
        return None

    if not response:
        return None

    # ignore short responses
    if len(response) < 80:
        return None

    # ignore casual conversation
    casual_words = [
        "hello",
        "hi",
        "thanks",
        "okay",
        "sure",
        "boss"
    ]

    text = response.lower()

    for word in casual_words:
        if word in text:
            return None
        
    if len(response) > 200:
        return response

    # store factual answers
    return response
