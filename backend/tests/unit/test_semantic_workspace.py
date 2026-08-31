from backend.app.agent.semantic_workspace import SemanticWorkspaceOutput, SemanticTarget, to_understanding


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
