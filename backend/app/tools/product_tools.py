from ..domain.product_service import search, get

def search_products(query: str = "", tags: list[str] | None = None):
    return search(query, tags)

def get_product(product_id: str):
    return get(product_id)
