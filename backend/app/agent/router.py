from .contracts import PlannerOutput
from ..tools.registry import execute

def route_action(output: PlannerOutput):
    if output.next_action.type == "TOOL_CALL":
        return execute(output.next_action.tool_name, output.next_action.arguments)
    return None
