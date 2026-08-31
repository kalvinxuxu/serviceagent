import json
from uuid import uuid4

from sqlalchemy import select

from .db.models.trace import AgentRun, AgentStep, ToolCall
from .db.session import SessionLocal, init_db


def begin_run(session_id: str) -> str:
    """Create a durable trace run for one customer turn."""
    init_db()
    run_id = uuid4().hex[:32]
    with SessionLocal() as db:
        db.add(AgentRun(id=run_id, session_id=session_id, status="RUNNING"))
        db.commit()
    return run_id


def record(session_id: str, step: dict, run_id: str | None = None) -> dict:
    """Persist a trace step and return the API-compatible representation."""
    init_db()
    run_id = run_id or begin_run(session_id)
    # Business identifiers (for example AgentTask.id) must not become the
    # database primary key of an AgentStep.
    item = {**step, "id": uuid4().hex[:8]}
    step_type = str(step.get("step_type", "unknown"))
    lineage = step.get("lineage") or {}
    with SessionLocal() as db:
        db.add(
            AgentStep(
                id=item["id"],
                run_id=run_id,
                step_type=step_type,
                output_summary=json.dumps(item, ensure_ascii=False),
                component=lineage.get("component") or step.get("component"),
                turn_id=str(step.get("turn_id")) if step.get("turn_id") is not None else None,
                input_snapshot=lineage.get("input", step.get("input", {})),
                output_snapshot=lineage.get("output", step.get("output", {})),
                before_state=lineage.get("before_state", step.get("before_state", {})),
                after_state=lineage.get("after_state", step.get("after_state", {})),
                latency_ms=lineage.get("latency_ms"),
                step_status=lineage.get("status") or step.get("status"),
                error_code=lineage.get("error_code") or step.get("error_code"),
            )
        )
        if step_type == "tool_call":
            db.add(
                ToolCall(
                    id=uuid4().hex[:32],
                    run_id=run_id,
                    tool_name=str(step.get("tool_name", "")),
                    arguments=step.get("arguments", {}),
                    result=step.get("result", {}),
                )
            )
        db.commit()
    return item


def record_agent_task(session_id: str, task: dict, run_id: str | None = None) -> dict:
    return record(session_id, {"step_type": "agent_task", "schema_version": "v2", **task}, run_id)


def record_agent_transition(session_id: str, transition: dict, run_id: str | None = None) -> dict:
    return record(session_id, {"step_type": "agent_transition", "schema_version": "v2", **transition}, run_id)


def finish_run(run_id: str, status: str) -> None:
    init_db()
    with SessionLocal() as db:
        run = db.get(AgentRun, run_id)
        if run:
            run.status = status
            db.commit()


def get(session_id: str, include_lineage: bool = False) -> list[dict]:
    """Read trace steps from the database, ordered by insertion."""
    init_db()
    with SessionLocal() as db:
        statement = (
            select(AgentStep.output_summary)
            .join(AgentRun, AgentRun.id == AgentStep.run_id)
            .where(AgentRun.session_id == session_id)
            .order_by(AgentStep.created_at, AgentStep.id)
        )
        items = [json.loads(summary) for summary in db.scalars(statement)]
        if not include_lineage:
            # Preserve the original trace contract for existing callers.
            items = [item for item in items if item.get("step_type") not in {"lineage", "turn_evaluation"}]
        return items
