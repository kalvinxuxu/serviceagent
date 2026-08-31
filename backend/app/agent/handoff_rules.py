def should_handoff(reason_code: str, customer_requested: bool = False) -> bool:
    return customer_requested or reason_code in {"CLARIFICATION_LOOP", "HUMAN_REQUEST_OR_HIGH_RISK", "TOOL_UNAVAILABLE"}
