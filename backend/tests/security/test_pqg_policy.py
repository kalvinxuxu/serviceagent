from backend.app.pqg.contracts import PQGRequest
from backend.app.pqg.service import clear_results, generate_suggestions


def test_pqg_suppresses_sensitive_or_high_risk_context():
    clear_results()
    result = generate_suggestions(PQGRequest(session_id="safe", assistant_message_id="m", context="顾客投诉食品安全问题", reply="转人工处理中"))
    assert result.status.value == "SUPPRESSED"
    assert result.questions == []
