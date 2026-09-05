from .multi_agent_contracts import SupervisorTask


COMMERCE_GOALS = {"INVENTORY_CHECK", "PRICE_CALCULATION", "RECOMMENDATION", "PRODUCT_SEARCH", "PRODUCT_BROWSE", "PRODUCT_COMPARE", "PRODUCT_FIT_QUERY", "PRODUCT_RECOMMENDATION", "SHIPPING_POLICY", "PROMOTION_QUERY", "MEMBERSHIP_PRICING", "FAQ", "RESERVATION"}
AFTER_SALES_GOALS = {"RETURN", "ORDER_STATUS", "COMPLAINT", "AFTER_SALES"}


def route_domain(goals: list[str]) -> str:
    """Converged domain routing; it never creates tasks or actions."""
    goal_set = set(goals)
    if goal_set & AFTER_SALES_GOALS:
        return "AFTER_SALES"
    if goal_set & COMMERCE_GOALS:
        return "COMMERCE"
    return "UNKNOWN"


# Legacy-only adapters.  Converged mode must call route_domain and leave task
# creation/action selection to Planner and Executor respectively.
legacy_build_tasks = None
legacy_route_action = None


def build_tasks(goals: list[str]) -> list[SupervisorTask]:
    tasks: list[SupervisorTask] = []
    commerce_index = 0
    after_sales_index = 0
    for goal in goals:
        if goal in COMMERCE_GOALS:
            commerce_index += 1
            tasks.append(SupervisorTask(id=f"commerce-{commerce_index}", target_agent="COMMERCE"))
        elif goal in AFTER_SALES_GOALS:
            after_sales_index += 1
            tasks.append(SupervisorTask(id=f"after-sales-{after_sales_index}", target_agent="AFTER_SALES"))
    return tasks


def route_action(goals: list[str], text: str) -> str:
    normalized = text.lower()
    if any(word in normalized for word in ("转人工", "人工客服", "真人客服")):
        return "HANDOFF"
    tasks = build_tasks(goals)
    if not tasks:
        return "ASK_USER"
    if len(tasks) > 1:
        return "PARALLEL_TASKS"
    return "CONTINUE_AGENT"


legacy_build_tasks = build_tasks
legacy_route_action = route_action
