from backend.app.agent.contracts import PendingFollowup
from backend.app.agent.followup_resolver import resolve_followup


def test_affirmative_reply_accepts_pending_followup():
    pending = PendingFollowup(type="RECOMMEND_PRODUCTS", source_turn_id="S:1", prompt="要不要我继续推荐？")
    assert resolve_followup("好的", pending).type == "ACCEPT_FOLLOWUP"


def test_affirmative_reply_without_pending_action_is_not_a_business_command():
    assert resolve_followup("好的", None).type == "NONE"


def test_rejection_closes_pending_followup():
    pending = PendingFollowup(type="RECOMMEND_PRODUCTS", source_turn_id="S:1", prompt="要不要我继续推荐？")
    assert resolve_followup("不用", pending).type == "REJECT_FOLLOWUP"
