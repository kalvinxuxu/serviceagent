from backend.app.agent.commerce_capabilities import COMMERCE_CAPABILITIES


def test_commerce_capabilities_do_not_include_unauthorized_side_effects():
    forbidden = {"refund", "compensate", "update_inventory", "catalog_maintenance"}
    assert not forbidden.intersection(COMMERCE_CAPABILITIES)
