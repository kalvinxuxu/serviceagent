from uuid import uuid4

from .state import CustomerServiceState


def ensure_goal(state: CustomerServiceState, goal_type: str, *, priority: int = 1) -> dict:
    active = next((goal for goal in state.goals if goal["type"] == goal_type and goal["status"] in {"ACTIVE", "PENDING", "PAUSED"}), None)
    if active:
        active["status"] = "ACTIVE"
        return active
    goal = {"id": f"goal_{uuid4().hex[:8]}", "type": goal_type, "status": "ACTIVE", "priority": priority}
    state.goals.append(goal)
    return goal

def transition_goals(state: CustomerServiceState, detected_goals: list[str], reason_code: str = "EXPLICIT_NEW_GOAL") -> list[dict]:
    desired = list(dict.fromkeys(detected_goals)) or ["OTHER"]
    transitions = []
    for goal in [item for item in state.goals if item["status"] == "ACTIVE"]:
        if goal["type"] not in desired:
            previous = goal["type"]
            goal["status"] = "COMPLETED"
            transitions.append({"previous_goal": previous, "detected_goal": desired[0], "transition": "SWITCH", "previous_goal_status": "COMPLETED", "new_goal_status": "ACTIVE", "reason_code": reason_code})
    for priority, goal_type in enumerate(desired, start=1):
        existing = next((goal for goal in state.goals if goal["type"] == goal_type and goal["status"] == "ACTIVE"), None)
        if existing:
            transitions.append({"previous_goal": goal_type, "detected_goal": goal_type, "transition": "CONTINUE", "previous_goal_status": "ACTIVE", "new_goal_status": "ACTIVE", "reason_code": "CURRENT_GOAL_CONTINUES"})
        else:
            ensure_goal(state, goal_type, priority=priority)
            transitions.append({"previous_goal": None, "detected_goal": goal_type, "transition": "CREATE", "previous_goal_status": None, "new_goal_status": "ACTIVE", "reason_code": reason_code})
    state.goal_transitions.extend(transitions)
    return transitions


def infer_goal_types(text: str) -> list[str]:
    goals = []
    generic_availability = any(word in text for word in ("还有什么", "还有哪些", "有什么", "哪些面包"))
    if any(word in text for word in ("多少钱", "多收钱", "合计", "总价", "一起要", "一共多少")):
        goals.append("PRICE_CALCULATION")
    if (
        text.strip() in {"贝果", "吐司", "欧包", "盐面包", "小面包"}
        or (any(category in text for category in ("贝果", "吐司", "欧包", "盐面包", "小面包"))
            and any(word in text for word in ("哪些", "什么", "都有", "有吗"))
            and "推荐" not in text)
    ):
        goals.append("INVENTORY_CHECK")
    if any(word in text for word in ("物流", "到哪", "订单状态")):
        goals.append("ORDER_STATUS")
    if any(word in text for word in ("退", "换")):
        goals.append("RETURN")
    broad_bread_inventory = generic_availability and "面包" in text and not any(word in text for word in ("推荐", "低糖", "孩子", "适合"))
    if any(word in text for word in ("推荐", "早餐", "低糖", "适合")) or (generic_availability and not broad_bread_inventory):
        goals.append("RECOMMENDATION")
    if broad_bread_inventory or (not generic_availability and (any(word in text for word in ("库存", "有货", "还有", "有没有", "是否有")) or ("有" in text and "吗" in text))):
        goals.append("INVENTORY_CHECK")
    return goals or ["OTHER"]


def update_goal_status(state: CustomerServiceState, status: str, goal_id: str | None = None) -> None:
    goal = next((item for item in state.goals if item["id"] == goal_id), None) if goal_id else next((item for item in reversed(state.goals) if item["status"] == "ACTIVE"), None)
    if goal:
        goal["status"] = status
