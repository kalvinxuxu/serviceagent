from backend.app.agent.semantic_workspace import SemanticWorkspaceOutput, SemanticTarget, to_understanding, understand_semantic
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed


def test_semantic_reference_is_converted_without_generating_sku():
    output = SemanticWorkspaceOutput(intent="SELECT_PRODUCT", target=SemanticTarget(type="REFERENCE", value="CHEAPEST"), operation="SELECT", quantity=2)
    understanding = to_understanding(output)
    assert understanding.references == ["CHEAPEST"]
    assert understanding.requested_items == []


def test_semantic_product_target_becomes_resolver_input_only():
    output = SemanticWorkspaceOutput(intent="ASK_PRICE", target=SemanticTarget(type="PRODUCT", value="芝士贝果"), operation="ADD", quantity=2)
    understanding = to_understanding(output)
    assert understanding.requested_items[0].query == "芝士贝果"
    assert understanding.requested_items[0].quantity == 2


def test_semantic_workspace_enriches_partial_llm_target_with_all_catalog_products(monkeypatch):
    load_products_from_seed()

    class Provider:
        async def structured_generate(self, **kwargs):
            return SemanticWorkspaceOutput(
                intent="ASK_PRICE",
                target=SemanticTarget(type="PRODUCT", value="原味吐司"),
                operation="SELECT",
                quantity=1,
                confidence=0.9,
            )

    monkeypatch.setattr("backend.app.agent.semantic_workspace.get_provider", lambda: Provider())
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    output = understand_semantic(
        CustomerServiceState(session_id="semantic-multi-product"),
        "原味吐司（14元），蔓越莓吐司（17元）各要1个，多少钱？",
    )
    assert {item["query"] for item in output.items} == {"原味吐司", "蔓越莓吐司"}
