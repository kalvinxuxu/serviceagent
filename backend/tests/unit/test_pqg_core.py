from backend.app.pqg.contracts import PQGRequest, PQGStatus
from backend.app.pqg.generation import parse_generation
from backend.app.pqg.policy import filter_candidates, suppression_reason
from backend.app.pqg.service import clear_results, generate_suggestions


def test_pqg_generates_at_most_three_and_is_cached():
    clear_results()
    request = PQGRequest(session_id="s", assistant_message_id="m", context="全麦吐司库存", reply="有货")
    result = generate_suggestions(request)
    assert result.status is PQGStatus.READY
    assert len(result.questions) <= 3
    assert generate_suggestions(request).request_id == result.request_id


def test_generation_rejects_non_versioned_payload():
    try:
        parse_generation({"questions": []})
    except ValueError as exc:
        assert "SCHEMA" in str(exc)
    else:
        raise AssertionError("invalid payload accepted")


def test_policy_suppresses_handoff_and_claims():
    assert suppression_reason("我要转人工", "好的")
    result = generate_suggestions(PQGRequest(session_id="s2", assistant_message_id="m", context="价格", reply="请问"))
    assert all("保证" not in item.text for item in result.questions)
