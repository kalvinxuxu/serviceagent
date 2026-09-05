import re
from .contracts import QuestionCandidate

_BLOCKED = ("身份证", "银行卡", "密码", "验证码", "强制购买", "马上付款", "保证最低价")
_FACT_CLAIMS = ("现货", "一定", "保证", "包邮", "今天送达", "最低价")


def suppression_reason(context: str, reply: str) -> str | None:
    text = f"{context} {reply}"
    if any(word in text for word in ("转人工", "投诉", "不要推荐", "别推荐", "停止推荐")):
        return "SUPPRESSION_POLICY"
    if any(word in text for word in ("食品安全", "过敏", "欺诈", "退款纠纷")):
        return "HIGH_RISK_CONTEXT"
    return None


def filter_candidates(candidates: list[QuestionCandidate], context: str, reply: str) -> list[QuestionCandidate]:
    current = re.sub(r"\W", "", context).lower()
    accepted: list[QuestionCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        text = candidate.text.strip()
        normalized = re.sub(r"\W", "", text).lower()
        if not text or normalized in seen or normalized in current:
            continue
        if any(word in text for word in _BLOCKED) or any(word in text for word in _FACT_CLAIMS):
            continue
        seen.add(normalized)
        accepted.append(candidate.model_copy(update={"rank": len(accepted) + 1}))
        if len(accepted) == 3:
            break
    return accepted
