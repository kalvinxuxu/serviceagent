import time
from datetime import datetime, timezone
from uuid import uuid4

from .contracts import PQGRequest, PQGResponse, PQGStatus, CandidateSource, QuestionCandidate
from .generation import generate_with_provider
from .repositories import save_result
from .policy import filter_candidates, suppression_reason
from .retrieval import retrieve

_RESULTS: dict[tuple[str, str], PQGResponse] = {}


def generate_suggestions(request: PQGRequest, llm=None) -> PQGResponse:
    started = time.perf_counter()
    key = (request.session_id, request.assistant_message_id)
    if not request.force_refresh and key in _RESULTS:
        return _RESULTS[key]
    suppressed = suppression_reason(request.context, request.reply)
    if suppressed:
        result = _response(request, PQGStatus.SUPPRESSED, [], started, suppressed)
        save_result(result)
        return result
    candidates = retrieve(f"{request.context}\n{request.reply}")
    error_code = None
    try:
        generated = (llm or generate_with_provider)(request.context, request.reply)
        candidates.extend(generated)
    except (ValueError, TypeError, TimeoutError, RuntimeError) as exc:
        error_code = str(exc)[:80] or "LLM_ERROR"
    accepted = filter_candidates(candidates, request.context, request.reply)
    status = PQGStatus.READY if accepted else (PQGStatus.DEGRADED if error_code else PQGStatus.EMPTY)
    result = _response(request, status, accepted, started, error_code)
    save_result(result)
    return result


def _response(request: PQGRequest, status: PQGStatus, questions: list[QuestionCandidate], started: float, error_code: str | None) -> PQGResponse:
    return PQGResponse(request_id=f"pqg_{uuid4().hex[:10]}", session_id=request.session_id, assistant_message_id=request.assistant_message_id, status=status, questions=questions[:3], generated_at=datetime.now(timezone.utc).isoformat(), latency_ms=round((time.perf_counter() - started) * 1000, 2), error_code=error_code)


def clear_results() -> None:
    _RESULTS.clear()
