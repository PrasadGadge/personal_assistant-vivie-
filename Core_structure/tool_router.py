# ==========================================
# Core_structure/tool_router.py
# Fixed: ValueError on unknown tool,
#        unhandled tool exceptions,
#        added list_tools() for debugging
# ==========================================

class ToolRouter:

    def __init__(self):
        self.tools = {}

    def register(self, name: str, func) -> None:
        """Register a callable tool by name."""
        self.tools[name] = func
        print(f"[ToolRouter] Registered: {name}")

    def execute(self, name: str, *args, **kwargs):
        """
        Execute a registered tool.

        FIX 1: Unknown tool now returns None instead of raising
        ValueError — prevents crashing the response pipeline when
        a planner suggests a tool that isn't registered yet.

        FIX 2: Tool exceptions are caught and logged — a broken
        tool no longer kills the entire request.

        Returns the tool's result, or None on any failure.
        """
        if name not in self.tools:
            # Log it so we can spot missing registrations — but don't crash
            print(f"[ToolRouter] Unknown tool: '{name}' — skipping")
            return None

        try:
            result = self.tools[name](*args, **kwargs)
            print(f"[ToolRouter] Executed: {name}")
            return result
        except Exception as e:
            print(f"[ToolRouter] Tool '{name}' raised: {e}")
            return None

    def list_tools(self) -> list:
        """Return names of all registered tools (useful for debugging)."""
        return list(self.tools.keys())

    def is_registered(self, name: str) -> bool:
        """Check if a tool is registered without executing it."""
        return name in self.tools
