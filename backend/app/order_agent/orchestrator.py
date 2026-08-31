from .contracts import OrderAction

ALLOWED_ACTIONS = {"PARSE_EMAIL", "CHECK_ORDER", "ASK_USER", "GENERATE_DRAFT", "ASK_CONFIRMATION", "SEND_REPLY", "HANDOFF"}

def validate_action(payload: dict) -> OrderAction:
    action = OrderAction.model_validate(payload)
    if action.action not in ALLOWED_ACTIONS:
        raise ValueError("UNSAFE_ACTION")
    return action

def next_action(*, stage: str, draft_id: str, confirmed: bool = False) -> OrderAction:
    if stage == "received": return OrderAction(action="PARSE_EMAIL", arguments={"draft_id": draft_id})
    if stage == "parsed": return OrderAction(action="CHECK_ORDER", arguments={"draft_id": draft_id})
    if stage == "checked": return OrderAction(action="GENERATE_DRAFT", arguments={"draft_id": draft_id})
    if stage == "ready" and not confirmed: return OrderAction(action="ASK_CONFIRMATION", arguments={"draft_id": draft_id})
    if stage == "ready" and confirmed: return OrderAction(action="SEND_REPLY", arguments={"draft_id": draft_id})
    return OrderAction(action="HANDOFF", arguments={"draft_id": draft_id})
