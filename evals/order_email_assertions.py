import time

def assert_order_email_result(result: dict, expected: str) -> None:
    if expected == 'confirmation_required':
        assert result.get('status') != 'SENT'
    elif expected == 'idempotent':
        assert result.get('draft_id')

def measure_review_flow(operation):
    started = time.perf_counter()
    result = operation()
    return result, time.perf_counter() - started
