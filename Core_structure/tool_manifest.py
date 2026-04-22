# ==================================================
# tool_manifest.py — Vivie Tool Integration Framework
# Drop one file → tool auto-discovered and registered
# ==================================================

import os
import json
import importlib
import logging
from typing import Optional, List, Dict

logger = logging.getLogger("ToolManifest")

# ─────────────────────────────────────────────────
# TOOL REGISTRY — single source of truth
# ─────────────────────────────────────────────────

_registry: dict = {}


class ToolManifest:
    """
    Base class for every Vivie tool.
    Inherit this and define metadata + handler.

    Example:
        class WeatherTool(ToolManifest):
            name        = "weather"
            description = "Get weather for a city"
            keywords    = ["weather", "temperature", "forecast"]
            action_type = "get_weather"
            subtypes    = ["forecast", "temperature"]

            @staticmethod
            def handler(details: str, **kwargs):
                from Features.weather_system import speak_weather
                city = kwargs.get("city")
                speak_weather(city)
                return "Weather fetched."
    """

    # ── Required fields ───────────────────────────
    name:        str  = ""       # unique tool name
    description: str  = ""       # what it does
    keywords:    list = []       # trigger words
    action_type: str  = ""       # planner action type
    subtypes:    list = []       # optional subtypes
    enabled:     bool = True     # can disable without deleting

    # ── Optional ──────────────────────────────────
    confidence_threshold: float = 0.75
    requires_online:      bool  = False
    category:             str   = "general"

    @staticmethod
    def handler(details: str, **kwargs) -> str:
        """Override this with actual tool logic."""
        raise NotImplementedError("Tool handler not implemented.")

    @classmethod
    def to_dict(cls) -> dict:
        return {
            "name":        cls.name,
            "description": cls.description,
            "keywords":    cls.keywords,
            "action_type": cls.action_type,
            "subtypes":    cls.subtypes,
            "enabled":     cls.enabled,
            "category":    cls.category,
            "handler":     cls.handler
        }


# ─────────────────────────────────────────────────
# REGISTER A TOOL MANUALLY
# ─────────────────────────────────────────────────

def register_tool(tool_class: type):
    """Register a tool class into the registry."""
    if not tool_class.name:
        logger.warning(f"[ToolManifest] Tool has no name — skipping.")
        return
    if not tool_class.enabled:
        logger.info(f"[ToolManifest] Tool '{tool_class.name}' is disabled — skipping.")
        return
    _registry[tool_class.name] = tool_class
    logger.info(f"[ToolManifest] Registered: '{tool_class.name}'")


# ─────────────────────────────────────────────────
# AUTO DISCOVER ALL TOOLS
# Scans Features/ and Tools/ for ToolManifest subclasses
# ─────────────────────────────────────────────────

def discover_tools(tool_dirs: Optional[List[str]] = None):
    """
    Auto-discover all tools by scanning tool directories.
    Looks for any class inheriting ToolManifest.
    """
    if tool_dirs is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tool_dirs = [
            os.path.join(base, "Features"),
            os.path.join(base, "Tools"),       # future tools folder
        ]

    found = 0
    for folder in tool_dirs:
        if not os.path.exists(folder):
            continue

        for fname in os.listdir(folder):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue

            module_name = fname[:-3]
            folder_name = os.path.basename(folder)

            try:
                module = importlib.import_module(f"{folder_name}.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, ToolManifest) and
                        attr is not ToolManifest and
                        attr.name):
                        register_tool(attr)
                        found += 1
            except Exception:
                pass  # silent — file might not have tools

    logger.info(f"[ToolManifest] Discovery complete. {found} tools found.")
    return found


# ─────────────────────────────────────────────────
# GET TOOL
# ─────────────────────────────────────────────────

def get_tool(name: str) -> Optional[type]:
    return _registry.get(name)


def get_all_tools() -> dict:
    return dict(_registry)


def get_tools_by_category(category: str) -> list:
    return [t for t in _registry.values() if t.category == category]


# ─────────────────────────────────────────────────
# EXECUTE A TOOL BY ACTION TYPE
# ─────────────────────────────────────────────────

def execute_tool(action_type: str, details: str, **kwargs) -> str:
    """
    Execute a tool by its action_type.
    Returns response string or empty string if not found.
    """
    for tool in _registry.values():
        if tool.action_type == action_type and tool.enabled:
            try:
                result = tool.handler(details, **kwargs)
                return result or ""
            except Exception as e:
                logger.error(f"[ToolManifest] Error executing '{tool.name}': {e}")
                return ""
    return ""


# ─────────────────────────────────────────────────
# INJECT INTO EXISTING SYSTEMS
# Call once at startup
# ─────────────────────────────────────────────────

def inject_into_intent_engine(intent_engine) -> None:
    """
    Automatically inject all tool keywords into IntentEngine.
    No manual editing of intent_engine.py ever again.
    """
    for tool in _registry.values():
        if tool.keywords:
            # Add to intent engine's keyword dict
            if hasattr(intent_engine, 'intents'):
                if tool.name not in intent_engine.intents:
                    intent_engine.intents[tool.name] = tool.keywords
                else:
                    # Merge keywords
                    existing = set(intent_engine.intents[tool.name])
                    new      = set(tool.keywords)
                    intent_engine.intents[tool.name] = list(existing | new)

        if tool.subtypes and hasattr(intent_engine, 'subtypes'):
            if tool.name not in intent_engine.subtypes:
                intent_engine.subtypes[tool.name] = tool.subtypes

    logger.info(f"[ToolManifest] Injected {len(_registry)} tools into IntentEngine.")


def inject_into_planner(planner) -> None:
    """
    Automatically inject all tool action types into Planner.
    No manual editing of plan.py ever again.
    """
    if not hasattr(planner, '_tool_registry'):
        planner._tool_registry = {}

    for tool in _registry.values():
        planner._tool_registry[tool.name] = tool.action_type

    logger.info(f"[ToolManifest] Injected {len(_registry)} tools into Planner.")


def inject_into_tool_router(tool_router) -> None:
    """
    Automatically register all tool handlers into ToolRouter.
    No manual registration in main_brain.py ever again.
    """
    for tool in _registry.values():
        tool_router.register(tool.action_type, tool.handler)

    logger.info(f"[ToolManifest] Injected {len(_registry)} tools into ToolRouter.")