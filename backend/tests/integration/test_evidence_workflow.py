from fastapi.testclient import TestClient

from backend.app.main import app


def test_address_in_observed_facts_is_normalized(monkeypatch):
    from backend.app.agent.evidence_service import _candidate_from_facts

    result = _candidate_from_facts({
        "classification": "UNCLASSIFIED",
        "observed_facts": ["图片中识别到收货地址：广东省清远市佛冈县明珠花园401"],
    })

    assert result["address_candidate"] == "广东省清远市佛冈县明珠花园401"


def test_address_image_requires_confirmation_then_commits(monkeypatch):
    monkeypatch.setattr("backend.app.api.sessions.save_attachment", lambda *args, **kwargs: {"attachment_id": "ATT_TEST", "filename": "address.png", "mime_type": "image/png", "path": "unused"})
    monkeypatch.setattr("backend.app.api.sessions.observe_attachment", lambda attachment: {
        "evidence_id": "EV_ADDRESS", "classification": "ADDRESS", "confidence": 0.98,
        "address_candidate": "广东省清远市佛冈县明珠花园401", "observed_facts": [], "uncertainties": [],
    })
    client = TestClient(app)
    session = client.post("/api/v1/sessions", json={"customer_id": "CUS001"}).json()["session_id"]
    response = client.post(f"/api/v1/sessions/{session}/messages", files={"attachments": ("address.png", b"image", "image/png")}, data={"message": ""})
    assert response.status_code == 200
    assert response.json()["requires_confirmation"] is True
    assert "确认" in response.json()["message"]["content"]
    response = client.post(f"/api/v1/sessions/{session}/messages", json={"message": "确认"})
    assert response.status_code == 200
    assert response.json()["inspector"]["reason_code"] == "EVIDENCE_COMMITTED"
    assert "省内支持顺丰" in response.json()["message"]["content"]
    session_data = client.get(f"/api/v1/sessions/{session}").json()
    assert session_data["delivery_slots"]["delivery_address"].startswith("广东省")


def test_quality_image_goes_to_human(monkeypatch):
    monkeypatch.setattr("backend.app.api.sessions.save_attachment", lambda *args, **kwargs: {"attachment_id": "ATT_TEST2", "filename": "damage.png", "mime_type": "image/png", "path": "unused"})
    monkeypatch.setattr("backend.app.api.sessions.observe_attachment", lambda attachment: {
        "evidence_id": "EV_DAMAGE", "classification": "FOOD_SAFETY_RISK", "confidence": 0.96,
        "observed_facts": ["疑似发霉"], "uncertainties": [],
    })
    client = TestClient(app)
    session = client.post("/api/v1/sessions", json={"customer_id": "CUS001"}).json()["session_id"]
    response = client.post(f"/api/v1/sessions/{session}/messages", files={"attachments": ("damage.png", b"image", "image/png")}, data={"message": "这个面包有问题"})
    assert response.status_code == 200
    assert response.json()["requires_human"] is True
    assert response.json()["status"] == "HANDOFF"


def test_logistics_match_requires_customer_authorization():
    from backend.app.agent.evidence_service import match_order, simulated_logistics
    assert match_order({"order_id_candidate": "ORD001"}, "OTHER") ["authorized"] is False
    assert match_order({"order_id_candidate": "ORD001"}, "CUS001")["authorized"] is True
    assert simulated_logistics("ORD002")["data"]["status"] == "IN_TRANSIT"
