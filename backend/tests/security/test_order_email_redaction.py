from backend.app.order_agent.trace import record
def test_trace_context_is_minimal():
    event=record('redact-001','TEST','test',context={'item_count':1})
    assert 'body' not in event['redacted_context']
