# ==================================================
# response_formatter.py — Vivie Personality Layer
# Fixed: opener duplication, em dash cleanup,
#        broader prefix detection
# ==================================================

import re
import random


# ─────────────────────────────────────────────────
# TONE PROFILES
# ─────────────────────────────────────────────────

TONE_PROFILES = {
    "casual": {
        "openers":       ["Boss,", "Hey Boss,", "Sure Boss,"],
        "max_sentences": 3
    },
    "technical": {
        "openers":       ["Boss,", "Boss, technically speaking,", "Here's the breakdown Boss,"],
        "max_sentences": 12
    },
    "factual": {
        "openers":       ["Boss,", "To answer that Boss,", "Boss, simply put,"],
        "max_sentences": 5
    },
    "memory": {
        "openers":       ["Boss,", "From what I remember Boss,", "Based on what you've told me Boss,"],
        "max_sentences": 6
    },
    "advisory": {
        "openers":       ["Boss,", "My recommendation Boss,", "Boss, here's what I think,"],
        "max_sentences": 6
    },
    "emotional": {
        "openers":       ["Boss,", "I hear you Boss,"],
        "max_sentences": 4
    },
    "comparative": {
        "openers":       ["Boss,", "Boss, here's the comparison,", "To compare Boss,"],
        "max_sentences": 12
    }
}


# ─────────────────────────────────────────────────
# STEP 1 — CLEAN ROBOTIC AI PHRASES
# ─────────────────────────────────────────────────

def _clean_robotic_phrases(text: str) -> str:
    robotic_phrases = [
        "As an AI language model,", "As an AI,", "I am an AI", "I'm an AI",
        "As a large language model,", "As an AI assistant,",
        "I am just an AI", "I'm just an AI",
        "I don't have feelings", "I don't have personal opinions",
        "I cannot provide personal opinions",
        "Certainly! ", "Certainly, ", "Of course! ", "Of course, ",
        "Absolutely! ", "Absolutely, ", "Great question! ",
        "That's a great question! ", "That's a great question, ",
        "I'd be happy to help! ", "I'd be happy to help, ",
        "I'd be happy to assist! ", "I'd be happy to assist, ",
        "Feel free to ask! ", "Feel free to ask, ",
        "Sure thing! ", "Sure thing, ",
    ]
    for phrase in robotic_phrases:
        text = text.replace(phrase, "")
        text = text.replace(phrase.lower(), "")
        text = text.replace(phrase.upper(), "")
    return text.strip()


# ─────────────────────────────────────────────────
# STEP 2 — NATURALIZE MEMORY REFERENCES
# ─────────────────────────────────────────────────

def _naturalize_memory_references(text: str) -> str:
    replacements = {
        "Based on stored memory data,":         "From what I remember,",
        "Based on stored memory data":          "From what I remember",
        "According to my memory,":              "From what I remember,",
        "According to my memory":               "From what I remember",
        "Based on your stored preferences,":    "Since you prefer,",
        "Based on your stored preferences":     "Since you prefer",
        "My records indicate,":                 "From what you've told me,",
        "My records indicate":                  "From what you've told me",
        "According to stored information,":     "Based on what I know about you,",
        "According to stored information":      "Based on what I know about you",
        "Based on the information I have,":     "From what I know,",
        "Based on the information I have":      "From what I know",
        "As per my records,":                   "From what I remember,",
        "As per my records":                    "From what I remember",
    }
    for robotic, natural in replacements.items():
        text = text.replace(robotic, natural)
    return text


# ─────────────────────────────────────────────────
# STEP 3 — DETECT TONE
# ─────────────────────────────────────────────────

def _detect_tone(text: str) -> str:
    t = text.lower()

    memory_signals = [
        "you told me", "you mentioned", "i remember", "from what i know",
        "you said", "you like", "you love", "your name", "you work",
        "you study", "you prefer", "here's what i recall", "what i recall",
        "i recall about you", "based on what you've told me",
        "interests:", "education:", "location:", "upcoming event",
        "here's what i know about you"
    ]
    if any(w in t for w in memory_signals):
        return "memory"

    comparative_signals = [
        "vs", "versus", "compared to", "on the other hand",
        "difference between", "in contrast", "whereas",
        "while", "both", "however", "ml is", "dl is"
    ]
    if any(w in t for w in comparative_signals):
        return "comparative"

    technical_signals = [
        "algorithm", "neural", "function", "code", "python",
        "machine learning", "deep learning", "architecture",
        "database", "api", "system", "pipeline", "model",
        "framework", "library", "syntax", "parameter",
        "backpropagation", "activation", "layer", "weight",
        "training", "dataset", "network", "computation",
        "input", "output", "node", "neuron"
    ]
    if any(w in t for w in technical_signals):
        return "technical"

    advisory_signals = [
        "i recommend", "you should", "best option",
        "i suggest", "my advice", "go with", "consider",
        "better choice", "is the better", "would recommend",
        "best approach", "ideal choice", "go for"
    ]
    if any(w in t for w in advisory_signals):
        return "advisory"

    emotional_signals = [
        "sorry", "understand", "difficult", "hard time",
        "feel", "support", "here for you", "tough",
        "struggle", "worried", "anxious", "stressed"
    ]
    if any(w in t for w in emotional_signals):
        return "emotional"

    factual_signals = [
        "is defined as", "refers to", "means that",
        "was born", "founded in", "located in",
        "is a tech", "is an entrepreneur", "is a ceo",
        "is the founder", "is known for", "is a company",
        "%", "million", "billion", "trillion",
        "kilometers", "years old", "established in"
    ]
    if any(w in t for w in factual_signals):
        return "factual"

    return "casual"


# ─────────────────────────────────────────────────
# STEP 4 — ADAPT LENGTH
# ─────────────────────────────────────────────────

def _adapt_length(text: str, tone: str) -> str:
    if tone in ["technical", "comparative", "factual", "memory", "advisory"]:
        return text

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    max_s     = TONE_PROFILES.get(tone, TONE_PROFILES["casual"])["max_sentences"]

    if len(sentences) > max_s:
        trimmed = " ".join(sentences[:max_s])
        if trimmed and trimmed[-1] not in ".!?":
            trimmed += "."
        return trimmed

    return text


# ─────────────────────────────────────────────────
# STEP 5 — ADD SMART OPENER
# FIX: broader prefix check — catches "hey", "sure",
#      "from", "based", "boss" regardless of what
#      follows (em dashes, commas, spaces, etc.)
# ─────────────────────────────────────────────────

# Words that signal an opener is already present
_OPENER_PREFIXES = (
    "boss", "hey", "sure", "from what", "based on",
    "my recommendation", "i hear you", "to compare",
    "to answer", "here's the breakdown",
)

def _has_opener(text: str) -> bool:
    """Return True if the text already starts with an opener."""
    t = text.lower().strip()
    return any(t.startswith(p) for p in _OPENER_PREFIXES)


def _add_opener(text: str, tone: str) -> str:
    if _has_opener(text):
        return text
    profile = TONE_PROFILES.get(tone, TONE_PROFILES["casual"])
    opener  = random.choice(profile["openers"])
    return f"{opener} {text}"


# ─────────────────────────────────────────────────
# STEP 6 — CLEAN REDUNDANT ENDINGS
# ─────────────────────────────────────────────────

def _clean_ending(text: str) -> str:
    redundant_endings = [
        "Let me know if you need anything else.",
        "Let me know if you need anything else!",
        "Feel free to ask if you have more questions.",
        "Feel free to ask if you have more questions!",
        "Let me know if you'd like more information.",
        "Let me know if you'd like more information!",
        "Is there anything else I can help you with?",
        "Is there anything else I can assist you with?",
        "Hope this helps!", "Hope that helps!", "Hope this was helpful!",
        "Let me know if you'd like to update or expand this information.",
        "Let me know if you'd like a deeper dive into any specific aspect.",
        "Let me know if you'd like more details.",
        "Let me know if you need further assistance.",
        "Let me know if you'd like to explore any of these further.",
        "Let me know if you want more details.",
        "Let me know if you'd like to dive deeper.",
        "Would you like to know more?",
        "Do you have any questions?", "Any questions?",
    ]

    text = text.strip()
    for ending in redundant_endings:
        if text.endswith(ending):
            text = text[:-len(ending)].strip()

    for ending in redundant_endings:
        ending_clean = ending.rstrip(".!?")
        if ending_clean.lower() in text.lower():
            idx = text.lower().rfind(ending_clean.lower())
            if idx > len(text) * 0.7:
                text = text[:idx].strip()

    if text and text[-1] not in ".!?":
        text += "."

    return text.strip()


# ─────────────────────────────────────────────────
# STEP 7 — FINAL CLEANUP
# FIX: added em dash cleanup + broader duplicate
#      opener removal
# ─────────────────────────────────────────────────

def _final_cleanup(text: str) -> str:

    # FIX: remove em dash artifacts (—) at start of response
    # These appear when LLM says "Hey Boss,—great to see you"
    text = re.sub(r'(?i)(boss,?\s*)—\s*', r'\1 ', text)
    text = re.sub(r'^—\s*', '', text)

    # Fix double spaces
    text = re.sub(r'  +', ' ', text)

    # Fix double punctuation
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r'\?\?+', '?', text)
    text = re.sub(r'!!+', '!', text)

    # FIX: remove duplicate openers more broadly
    # Catches: "Hey Boss, Hey Boss,", "Boss, Boss,",
    #          "Sure Boss, Hey Boss,", "Hey Hey Boss,"
    text = re.sub(r'(?i)\bhey\s+hey\b', 'Hey', text)
    text = re.sub(r'(?i)(boss,?\s*){2,}', 'Boss, ', text)
    text = re.sub(r'(?i)(hey boss,?\s*){2,}', 'Hey Boss, ', text)
    text = re.sub(r'(?i)(sure boss,?\s*){2,}', 'Sure Boss, ', text)

    # Fix legacy patterns (these should rarely appear after step 1 cleanup)
    text = re.sub(r'(?i)hello[,.]?\s*prasad[,.]?\s*(boss,?)?', '', text)
    text = re.sub(r'(?i)boss,\s*hello,\s*prasad', 'Boss,', text)
    text = re.sub(r'(?i)boss,\s*here\'s the breakdown boss,',
                  "Here's the breakdown Boss,", text)

    # Clean up comma-space issues after fixes
    text = re.sub(r',\s{2,}', ', ', text)

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    return text.strip()


# ─────────────────────────────────────────────────
# MAIN FORMAT FUNCTION
# ─────────────────────────────────────────────────

def format_response(text: str) -> str:
    """
    Full Vivie personality formatting pipeline.
    Step 1 — Remove robotic AI phrases
    Step 2 — Naturalize memory references
    Step 3 — Detect tone
    Step 4 — Adapt length
    Step 5 — Add smart opener
    Step 6 — Remove redundant endings
    Step 7 — Final cleanup
    """
    if not text or not text.strip():
        return text

    text = _clean_robotic_phrases(text)
    text = _naturalize_memory_references(text)
    tone = _detect_tone(text)
    text = _adapt_length(text, tone)
    text = _add_opener(text, tone)
    text = _clean_ending(text)
    text = _final_cleanup(text)

    return text
