from backend.app.tools.return_tools import check_eligibility, create_request

def test_return_contract_requires_confirmation():
    assert check_eligibility("ORD001", "CUS001")["eligible"]
    assert create_request("ORD001", "CUS001", False)["reason"] == "CONFIRMATION_REQUIRED"
