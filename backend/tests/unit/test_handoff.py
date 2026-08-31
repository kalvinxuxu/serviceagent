from backend.app.agent.handoff_rules import should_handoff
from backend.app.domain.handoff_service import redact

def test_handoff_boundary_and_redaction():
    assert should_handoff("HUMAN_REQUEST_OR_HIGH_RISK")
    assert redact({"customer_id":"CUS001"})["customer_id"] == "***01"
