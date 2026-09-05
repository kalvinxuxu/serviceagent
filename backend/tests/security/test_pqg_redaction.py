from backend.app.pqg.contracts import PQGRequest
from backend.app.pqg.service import clear_results, generate_suggestions


def test_sensitive_context_does_not_create_suggestion_claims():
    clear_results()
    result = generate_suggestions(PQGRequest(session_id="redact", assistant_message_id="m", context="我的银行卡和验证码", reply="请不要处理敏感信息"))
    assert all("银行卡" not in question.text and "验证码" not in question.text for question in result.questions)
