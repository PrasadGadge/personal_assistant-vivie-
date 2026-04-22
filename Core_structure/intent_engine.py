# ==========================================
# Core_structure/intent_engine.py
# ==========================================

import re
from Core_structure.ai_intent import AIIntentDetector


class IntentEngine:
    """
    Smart intent detection engine for Vivie.
    Detects primary intent, subtype, and confidence level.
    """

    def __init__(self):
        self.ai_detector = AIIntentDetector()

        # ===============================
        # PRIMARY INTENTS
        # ===============================
        self.intents = {
            "chat": [
                "who is", "what is", "tell me about",
                "how old", "define", "explain",
                "meaning of"
            ],

            "vision": [
                "what can you see", "take a look",
                "analysis","analyse","analyze","what do you see"
            ],

            "weather": [
                "weather", "temperature",
                "forecast", "rain", "sunny", "snow"
            ],

            "image_generation": [
                "generate image", "draw",
                "create image", "make a picture",
                "illustrate"
            ],

            "alarm": [
                "set alarm", "alarm"
            ],

            "internet_speed": [
                "internet speed",
                "check internet speed",
                "network speed",
                "how fast is my internet"
            ],

            "automation": [
                "open", "close", "start",
                "run", "launch", "stop"
            ],

            "file_creation": [
                "create file", "new file",
                "make file",
                "file named", "file name",
                "create text file"
            ],

            "whatsapp": [
                "send message on whatsapp",
                "whatsapp message",
                "send whatsapp",
                "send message"
            ],

            "morning_brief":[
                "start my day",
                "morning briefing",
                "daily briefing",
                "morning report"
            ]
        }

        # ===============================
        # SUBTYPES
        # ===============================
        self.subtypes = {
            "weather": ["forecast", "temperature", "humidity", "rain"],
            "image_generation": ["image", "drawing", "illustration"],
            "chat": ["personal_info", "history", "knowledge", "math", "science"],
            "automation": ["system_control", "app_control", "web_control"],
            "file_creation": ["text", "python", "java", "document"],
            "alarm": ["set", "check"],
            "internet_speed": ["check", "report"],
            "whatsapp": ["send", "read"]
        }

    # ==========================================
    # DETECT FUNCTION
    # ==========================================

    def detect(self, text, context=None):

        # Normalize input
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()

        intent_detected = "unknown"
        subtype_detected = "general"
        confidence = 0.0

        # ======================================
        # STRONG REGEX MATCHING
        # ======================================

        # File creation detection
        if re.search(r"\b(create|make|new)\b.*\b(python|java|text)?\b.*\bfile\b", text):
            return {
                "primary": "file_creation",
                "subtype": "code_file",
                "confidence": 0.95
            }

        # WhatsApp message detection
        if re.search(r"\b(send|write)\b.*\b(whatsapp|message)\b", text):
            return {
                "primary": "whatsapp",
                "subtype": "send_message",
                "confidence": 0.95
            }

        # Weather detection priority
        if re.search(r"\b(weather|temperature|forecast)\b", text):
            return {
                "primary": "weather",
                "subtype": "forecast",
                "confidence": 0.95
            }

        # ======================================
        # SCORE-BASED KEYWORD MATCHING
        # ======================================

        scores = {}

        for intent, keywords in self.intents.items():
            score = 0

            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text):
                    score += 1

            if score > 0:
                scores[intent] = score

        if scores:
            intent_detected = max(scores, key=scores.get)
            confidence = min(0.95, 0.70 + scores[intent_detected] * 0.10)

        # ======================================
        # SUBTYPE DETECTION
        # ======================================

        if intent_detected != "unknown":
            subtype_keywords = self.subtypes.get(intent_detected, [])

            for st in subtype_keywords:
                if re.search(r"\b" + re.escape(st) + r"\b", text):
                    subtype_detected = st
                    break

        # Context continuation
        if intent_detected == "unknown" and context:
            last_intent = context.get("last_intent")
            follow_words = [
                "tomorrow",
                "today",
                "next",
                "and",
                "then",
                "what about",
                "how about"
            ]

            if any(word in text for word in follow_words):

                if last_intent == "weather":
                    return {
                        "primary": "weather",
                        "subtype": "forecast",
                        "confidence": 0.9
                    }

        # ======================================
        # AI FALLBACK
        # ======================================

        if intent_detected == "unknown":
            print("⚡ Switching to AI Intent Detection...")
            return self.ai_detector.detect(text)

        return {
            "primary": intent_detected,
            "subtype": subtype_detected,
            "confidence": confidence
        }