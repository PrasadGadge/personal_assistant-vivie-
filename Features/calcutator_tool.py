from Core_structure.tool_manifest import ToolManifest

class CalculatorTool(ToolManifest):
    name        = "calculator"
    description = "Perform mathematical calculations"
    keywords    = ["calculate", "what is", "how much is", "solve", "math"]
    action_type = "calculate"
    subtypes    = ["math", "arithmetic"]
    category    = "utility"

    @staticmethod
    def handler(details: str, **kwargs) -> str:
        from Brain.cl_brain import Main_Brain
        result = Main_Brain(f"Calculate this and give only the answer: {details}")
        return result or "Could not calculate."