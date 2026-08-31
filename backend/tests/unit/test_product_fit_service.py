from backend.app.domain.product_fit_service import explain_product_fit
from backend.app.db.seed import load_products_from_seed


def test_product_fit_uses_verified_audience_metadata():
    load_products_from_seed()
    result = explain_product_fit("SKU026", "儿童", "audience")
    assert result["product_name"] == "生吐司"
    assert result["fit_status"] in {"SUPPORTED", "UNKNOWN"}
    assert result["evidence"]


def test_product_fit_does_not_invent_texture():
    load_products_from_seed()
    result = explain_product_fit("SKU009", "老人", "texture")
    assert result["fit_status"] == "UNKNOWN"
    assert result["evidence"] == []
