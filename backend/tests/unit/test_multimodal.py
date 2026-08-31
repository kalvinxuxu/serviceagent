from backend.app.agent.multi_agent_contracts import EvidenceObservation
from backend.app.llm.multimodal import MultimodalEvidenceAdapter


def test_evidence_contract_preserves_address_candidates():
    observation = EvidenceObservation(
        source="IMAGE",
        classification="DELIVERY_ADDRESS",
        confidence=0.95,
        address_candidate="广东省清远市佛冈县明珠花园401",
        observed_at="runtime",
    )

    assert observation.model_dump()["address_candidate"].startswith("广东省清远市")


def test_qwen_vision_adapter_returns_observation_only(monkeypatch):
    class StubVisionProvider:
        async def structured_generate(self, *, messages, output_schema, temperature=0):
            assert output_schema is EvidenceObservation
            assert isinstance(messages[-1].content, list)
            return EvidenceObservation(
                source="IMAGE",
                classification="DAMAGED_PRODUCT",
                confidence=0.91,
                observed_facts=["包装有明显破损"],
                observed_at="runtime",
            )

    monkeypatch.setenv("VISION_PROVIDER", "aliyun")
    monkeypatch.setattr("backend.app.llm.multimodal.get_vision_provider", lambda: StubVisionProvider())

    result = MultimodalEvidenceAdapter().observe({"url": "data:image/png;base64,placeholder"})

    assert result["classification"] == "DAMAGED_PRODUCT"
    assert result["side_effect_allowed"] is False


def test_missing_image_url_does_not_call_vision_provider(monkeypatch):
    monkeypatch.setenv("VISION_PROVIDER", "aliyun")
    result = MultimodalEvidenceAdapter().observe({"filename": "damage.png"})
    assert result["classification"] == "UNCLASSIFIED"
    assert result["confidence"] == 0.0
