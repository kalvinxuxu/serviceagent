from fastapi.testclient import TestClient

from backend.app.main import app


def test_media_and_customer_memory_api_are_isolated():
    client = TestClient(app)
    media = client.get("/api/v1/media", params={"asset_type": "FEATURED_BOARD"})
    assert media.status_code == 200
    assert media.json()["items"]

    response = client.put("/api/v1/customers/CUS_MEDIA_TEST/memory", json={
        "type": "EXPLICIT_AVOIDANCE", "key": "flavor", "value": "CHOCOLATE"
    })
    assert response.status_code == 200
    assert client.get("/api/v1/customers/CUS_MEDIA_TEST/memory").json()["items"][0]["customer_id"] == "CUS_MEDIA_TEST"
    assert client.get("/api/v1/customers/CUS_OTHER/memory").json()["items"] == []


def test_admin_rejects_invalid_product_and_persists_featured_changes():
    client = TestClient(app)
    invalid = client.put("/api/v1/admin/products/SKU001", json={"price": -1})
    assert invalid.status_code == 422
    original = client.get("/api/v1/admin/featured-list").json()
    product_id = original["product_ids"][0]
    removed = client.delete(f"/api/v1/admin/featured-list/items/{product_id}")
    assert removed.status_code == 200
    restored = client.post(f"/api/v1/admin/featured-list/items/{product_id}")
    assert restored.status_code == 200
    assert product_id in restored.json()["product_ids"]
    assert client.get("/api/v1/admin/audit", params={"key": "featured_list"}).json()["items"]


def test_admin_media_upload_rejects_unsupported_type():
    client = TestClient(app)
    response = client.post("/api/v1/admin/media/upload", files={"file": ("menu.txt", b"not an image", "text/plain")})
    assert response.status_code == 422


def test_admin_benchmark_endpoint_returns_latest_report_when_available():
    client = TestClient(app)
    response = client.get("/api/v1/admin/benchmark/latest")
    assert response.status_code in {200, 404}
    if response.status_code == 200:
        assert "metrics" in response.json()


def test_admin_token_protects_maintenance_api(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")
    client = TestClient(app)
    assert client.get("/api/v1/admin/products").status_code == 401
    assert client.get("/api/v1/admin/products", headers={"X-Admin-Token": "test-admin-token"}).status_code == 200


def test_product_admin_list_has_table_contract_and_safe_filters():
    client = TestClient(app)
    response = client.get("/api/v1/admin/product-list", params={"sort_by": "price_asc"})
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert {"id", "name", "category", "dine_in_price", "display_discount_price", "inventory", "primary_media", "display_tags", "status"} <= set(item)
    assert "available_quantity" in item["inventory"]
    assert client.get("/api/v1/admin/product-list", params={"sort_by": "bad"}).status_code == 422

