def pqg_trace(result, *, filtered_count: int = 0) -> dict:
    return {"component": "pqg", "status": result.status.value, "source_count": len(result.questions), "filtered_count": filtered_count, "latency_ms": result.latency_ms, "error_code": result.error_code}
