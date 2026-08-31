def should_handoff(turn_count: int, reason_code: str) -> bool:
    return turn_count >= 3 or reason_code in {"HUMAN_REQUEST_OR_HIGH_RISK", "TOOL_UNAVAILABLE"}
