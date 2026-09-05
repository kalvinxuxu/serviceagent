from backend.app.pqg.contracts import PQGRequest
from time import perf_counter
from backend.app.pqg.service import clear_results, generate_suggestions
from backend.app.pqg.repositories import save_event


def main() -> None:
    clear_results()
    started = perf_counter()
    result = generate_suggestions(PQGRequest(session_id="eval", assistant_message_id="m", context="全麦吐司库存", reply="目前有货"))
    elapsed_ms = (perf_counter() - started) * 1000
    assert result.status.value in {"READY", "EMPTY", "DEGRADED"}
    assert len(result.questions) <= 3
    assert all(1 <= question.rank <= 3 for question in result.questions)
    assert elapsed_ms < 3000
    assert any(any(word in question.text for word in ("商品", "了解", "搭配", "早餐")) for question in result.questions)
    save_event("eval", result.request_id, result.questions[0].candidate_id if result.questions else "none", "CLICK")
    blocked = generate_suggestions(PQGRequest(session_id="eval", assistant_message_id="risk", context="我要投诉食品安全", reply="转人工"))
    assert blocked.status.value == "SUPPRESSED"
    print("PQG assertions passed")


if __name__ == "__main__":
    main()
