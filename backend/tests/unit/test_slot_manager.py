from backend.app.agent.slot_manager import missing_slots, next_clarification


def test_product_selection_asks_for_quantity_only_when_missing():
    request = next_clarification("SELECT_PRODUCT", {})
    assert request and request.next_slot == "quantity"
    assert request.missing_slots[0].prompt == "您需要几个呢？"
    assert missing_slots("SELECT_PRODUCT", {"quantity": 1}) == []


def test_delivery_slots_are_collected_in_order():
    request = next_clarification("CREATE_DELIVERY_REQUEST", {})
    assert [slot.name for slot in request.missing_slots] == ["delivery_address", "recipient_name", "phone"]
    request = next_clarification("CREATE_DELIVERY_REQUEST", {"delivery_address": "上海市"})
    assert request.next_slot == "recipient_name"
