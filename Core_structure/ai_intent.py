from Brain.system_llm import system_llm
import json
import re

class AIIntentDetector:

    def extract_json(self, text):
        match = re.search(r"\{.*\}",text,re.DOTALL)
        if match:
            return match.group()
        return None

    def detect(self, text):

        prompt = f"""
You are an intent classification engine.

Classify the user request into ONE of these categories:

- chat
- weather
- automation
- file_creation
- whatsapp
- image_generation
- internet_speed
- alarm

Return ONLY valid JSON like this:

Example format:

{{
  "primary": "intent_name",
  "subtype": "optional_detail",
  "confidence": 0.95
}}

User Input:
{text}
"""

        response = system_llm(prompt)

        try:
            json_text = self.extract_json(response)
            if not json_text:
                raise ValueError("NO JSON detected")
            
            intent = json.loads(json_text)
            if "primary" not in intent:
                raise ValueError("Missing primary intent")
            return intent
        
        except Exception as e:
            print("intent parse error:",e)
            return {
                "primary": "chat",
                "subtype": "general",
                "confidence": 0.6
            }