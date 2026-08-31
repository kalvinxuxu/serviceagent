from __future__ import annotations

from .contracts import FollowupIntent, PendingFollowup


ACCEPT_WORDS = {"好", "好的", "可以", "行", "好呀", "可以的", "那就这样", "按你说的来", "haode", "ok"}
REJECT_WORDS = {"不用", "不要", "算了", "先不用", "不需要"}


def resolve_followup(text: str, pending: PendingFollowup | dict | None) -> FollowupIntent:
    if not pending:
        return FollowupIntent()
    normalized = "".join(str(text).strip().split()).lower()
    if normalized in ACCEPT_WORDS:
        return FollowupIntent(type="ACCEPT_FOLLOWUP", confidence=1.0)
    if normalized in REJECT_WORDS:
        return FollowupIntent(type="REJECT_FOLLOWUP", confidence=1.0)
    return FollowupIntent(type="NONE")
