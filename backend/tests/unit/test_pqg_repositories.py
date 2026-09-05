from uuid import uuid4
from backend.app.pqg.contracts import PQGRequest
from backend.app.pqg.repositories import get_result
from backend.app.pqg.service import clear_results, generate_suggestions


def test_pqg_result_can_be_read_from_repository():
    clear_results()
    session_id = f"repo-{uuid4().hex[:8]}"
    request = PQGRequest(session_id=session_id, assistant_message_id="m", context="全麦吐司", reply="有货")
    result = generate_suggestions(request)
    clear_results()
    loaded = get_result(session_id, "m")
    assert loaded is not None and loaded.request_id == result.request_id
