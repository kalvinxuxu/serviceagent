import asyncio
import json
import threading
from typing import Any

from pydantic import BaseModel

from ..agent.multi_agent_contracts import EvidenceObservation
from .factory import get_vision_provider
from ..agent.state import Message


def _run(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result = []
    thread = threading.Thread(target=lambda: result.append(asyncio.run(coro)))
    thread.start()
    thread.join()
    return result[0]


class MultimodalEvidenceAdapter:
    """Visual evidence adapter; it observes facts but never decides policy."""

    def observe(self, attachment: dict[str, Any]) -> dict[str, Any]:
        image_url = attachment.get("data_url") or attachment.get("url")
        if not image_url:
            return {"source": "IMAGE", "metadata": attachment, "classification": "UNCLASSIFIED", "confidence": 0.0}
        try:
            metadata = {key: value for key, value in attachment.items() if key != "data_url"}
            observation = _run(get_vision_provider().structured_generate(
                messages=[
                    Message(
                        role="system",
                        content=(
                            "你是客服证据观察组件。只描述图片中可观察到的事实，" 
                            "不判断退款、赔偿或政策结果。请识别地址、订单号、快递单号；" 
                            "质量问题分类使用 PACKAGING_DAMAGE、PRODUCT_DAMAGE、QUALITY_DEFECT、" 
                            "FOOD_SAFETY_RISK 或 UNKNOWN_VISUAL_ISSUE。输出 address_candidate、" 
                            "order_id_candidate、tracking_number_candidate、carrier、observed_facts、" 
                            "uncertainties、classification 和 confidence。只输出 JSON。"
                        ),
                    ),
                    Message(
                        role="user",
                        content=[
                            {"type": "text", "text": json.dumps({"attachment": metadata}, ensure_ascii=False)},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    ),
                ],
                output_schema=EvidenceObservation,
                temperature=0,
            ))
            if isinstance(observation, BaseModel):
                return observation.model_dump()
            return observation
        except Exception as exc:
            return {
                "source": "IMAGE",
                "metadata": attachment,
                "classification": "UNCLASSIFIED",
                "confidence": 0.0,
                "uncertainties": [f"vision_provider_error:{type(exc).__name__}"],
            }
