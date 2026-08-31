from __future__ import annotations

import re
from typing import Any


def detect_feedback(text: str, previous: dict[str, Any] | None = None) -> dict[str, Any] | None:
    previous = previous or {}
    if re.search(r"不是.*(问|说|要的是).*(价格|多少钱|库存|有货)", text):
        corrected = "PRICE_CALCULATION" if re.search(r"价格|多少钱", text) else "INVENTORY_CHECK"
        return {"feedback_type": "CORRECTION", "target_component": "UNDERSTANDING", "previous_value": (previous.get("goals") or [None])[0], "corrected_value": corrected, "source": "USER_EXPLICIT", "confidence": 1.0, "raw_text": text}
    if re.search(r"(刚才|我已经|不是已经).*(说|告诉|问)了", text):
        return {"feedback_type": "CONTEXT_FAILURE", "target_component": "STATE_MANAGER", "source": "USER_IMPLICIT", "confidence": 0.9, "raw_text": text}
    if re.search(r"(都太贵|太贵了|便宜一点|便宜的)", text):
        return {"feedback_type": "NEGATIVE_PREFERENCE", "target_component": "CONSTRAINT_EXTRACTION", "corrected_value": {"budget_preference": "LOWER_PRICE"}, "source": "USER_IMPLICIT", "confidence": 0.85, "raw_text": text}
    if re.search(r"(再推荐|换一批|再来几款)", text):
        return {"feedback_type": "REFRESH_REQUEST", "target_component": "RECOMMENDATION", "source": "USER_EXPLICIT", "confidence": 1.0, "raw_text": text}
    return None
