from typing import Any
from uuid import uuid4

from .multi_agent_contracts import AgentTask, AgentName, TaskStatus
from .state import CustomerServiceState


def create_task(state: CustomerServiceState, target_agent: AgentName, task_type: str, context: dict[str, Any] | None = None) -> AgentTask:
    source = state.active_agent
    task = AgentTask(id=f"task-{uuid4().hex[:10]}", session_id=state.session_id, task_type=task_type, source_agent=source, target_agent=target_agent, relevant_context=context or {})
    state.task_stack.append(task.model_dump())
    return task


def update_task(state: CustomerServiceState, task_id: str, status: TaskStatus, reason: str | None = None) -> AgentTask | None:
    for item in state.task_stack:
        if item.get("id") == task_id:
            item["status"] = status
            item["blocked_reason"] = reason
            return AgentTask.model_validate(item)
    return None


def resume_task(state: CustomerServiceState, task_id: str) -> AgentTask | None:
    return update_task(state, task_id, "RUNNING")
