from __future__ import annotations

import asyncio
import json
import os
import threading
from typing import Any

from pydantic import BaseModel, Field

from backend.app.agent.state import Message
from backend.app.llm import get_provider


class JudgeOutput(BaseModel):
    clarity: int = Field(ge=0, le=1)
    directness: int = Field(ge=0, le=1)
    customer_friendly: int = Field(ge=0, le=1)
    explains_next_step: int = Field(ge=0, le=1)
    hallucination_risk: int = Field(ge=0, le=1)
    comment: str = ""


def _run(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result = []
    thread = threading.Thread(target=lambda: result.append(asyncio.run(coro)))
    thread.start(); thread.join()
    return result[0]


def judge_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    if os.getenv("BENCHMARK_LLM_JUDGE", "0") != "1":
        return None
    prompt = {"case": case, "reply": result.get("replies", [])[-1], "deterministic_scores": result["scores"], "trace": result.get("traces", [])}
    try:
        output = _run(get_provider().structured_generate(
            messages=[
                Message(role="system", content="你是客服回复质量评审。只评价表达清晰、直接、友好、下一步说明和是否疑似编造。价格、库存、政策和工具正确性必须以 deterministic_scores 为准，不能改写这些分数。只输出 JSON。"),
                Message(role="user", content=json.dumps(prompt, ensure_ascii=False)),
            ], output_schema=JudgeOutput, temperature=0,
        ))
        return output.model_dump()
    except Exception as exc:
        return {"error": type(exc).__name__}
