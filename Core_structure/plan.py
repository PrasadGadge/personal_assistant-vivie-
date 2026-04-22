# ==========================================
# plan.py — Upgraded with Tool Framework
# ==========================================

class Planner:

    def __init__(self):
        self._tool_registry = {}  # auto-populated by tool manifest

    def generate_plan(self, intent, context):
        actions  = []
        primary  = intent.get("primary",    "unknown")
        confidence = intent.get("confidence", 0.0)
        user_text  = context.get("last_input", "")

        # ── Automation ────────────────────────────
        if primary == "automation" and confidence >= 0.75:
            actions.append({"type": "automation", "details": user_text})
        elif primary == "automation":
            actions.append({"type": "respond_text", "details": f"Did you mean: {user_text}?"})

        # ── Weather ───────────────────────────────
        elif primary == "weather":
            t = "get_forecast" if "forecast" in user_text else "get_weather"
            actions.append({"type": t, "details": user_text})

        # ── Check tool registry for this intent ───
        elif primary in self._tool_registry:
            action_type = self._tool_registry[primary]
            actions.append({"type": action_type, "details": user_text})

        # ── Legacy hardcoded types ─────────────────
        elif primary == "file_creation":
            actions.append({"type": "create_file",          "details": user_text})
        elif primary == "internet":
            actions.append({"type": "check_internet_speed", "details": user_text})
        elif primary == "vision":
            actions.append({"type": "vision_analysis",      "details": user_text})
        elif primary == "whatsapp":
            actions.append({"type": "send_whatsapp",        "details": user_text})
        elif primary == "image_generation":
            actions.append({"type": "generate_image",       "details": user_text})

        # ── Fallback ──────────────────────────────
        if not actions:
            actions.append({"type": "respond_text", "details": user_text})

        return actions