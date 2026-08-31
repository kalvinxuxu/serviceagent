def retry_allowed(attempts: int, max_attempts: int = 2) -> bool:
    return attempts < max_attempts

def safe_tool_failure() -> dict:
    return {"status": "HANDOFF", "reason_code": "TOOL_UNAVAILABLE", "execute_side_effect": False}
