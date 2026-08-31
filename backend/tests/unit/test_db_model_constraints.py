from backend.app.db.models import Product, ReturnRequest

def test_entities_expose_required_constraints():
    assert Product.__tablename__ == "products"
    assert any(c.name == "uq_return_item_type_status" for c in ReturnRequest.__table__.constraints)
