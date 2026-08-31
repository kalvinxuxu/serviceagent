from backend.app.domain.return_service import check_return_eligibility

def test_return_window_rule():
    assert check_return_eligibility("ORD001", "CUS001")["eligible"]
    assert not check_return_eligibility("UNKNOWN", "CUS001")["eligible"]
