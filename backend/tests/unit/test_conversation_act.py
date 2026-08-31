from backend.app.agent.contracts import UnderstandingOutput


def test_understanding_contract_supports_selection_and_slots():
    output = UnderstandingOutput(
        goals=["PRODUCT_RECOMMENDATION"],
        conversation_act="SELECT",
        slot_values={"quantity": None},
    )
    assert output.conversation_act == "SELECT"
    assert output.slot_values["quantity"] is None
