import json
import re
import asyncio
from .contracts import CandidateSource, LLMGenerationOutput, QuestionCandidate
from ..llm.factory import get_provider
from ..agent.state import Message


def build_prompt(context: str, reply: str) -> list[dict[str, str]]:
    return [Message(role="system", content="只输出 pqg.v1 JSON，不要 Markdown。最多生成3个顾客可能追问的问题；不得编造价格、库存、优惠或配送承诺。"), Message(role="user", content=f"当前对话：{context[-4000:]}\n最后回复：{reply[-2000:]}")]


def parse_generation(raw: str | dict) -> list[QuestionCandidate]:
    if isinstance(raw, LLMGenerationOutput):
        raw = raw.model_dump(mode="json")
    payload = raw if isinstance(raw, dict) else json.loads(raw)
    if payload.get("schema_version") != "pqg.v1":
        raise ValueError("INVALID_SCHEMA_VERSION")
    questions = payload.get("questions")
    if not isinstance(questions, list) or len(questions) > 3:
        raise ValueError("INVALID_QUESTION_COUNT")
    result: list[QuestionCandidate] = []
    seen: set[str] = set()
    for index, item in enumerate(questions, 1):
        if not isinstance(item, dict) or set(item) - {"text", "reason"}:
            raise ValueError("INVALID_QUESTION_ITEM")
        text = str(item.get("text", "")).strip()
        key = re.sub(r"\W", "", text).lower()
        if len(text) < 2 or not key or key in seen:
            continue
        seen.add(key)
        result.append(QuestionCandidate(candidate_id=f"llm-{index}", text=text, source=CandidateSource.LLM, rank=len(result) + 1))
    return result


def generate_with_provider(context: str, reply: str) -> list[QuestionCandidate]:
    provider = get_provider()
    output = asyncio.run(provider.structured_generate(messages=build_prompt(context, reply), output_schema=LLMGenerationOutput, temperature=0.2))
    return parse_generation(output)
