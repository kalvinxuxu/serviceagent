from ..domain.recommendation_service import recommend, relaxation_options

def recommend_products(tags: list[str] | None = None, category: str | None = None, max_price: float | None = None, exclude_tags: list[str] | None = None, categories: list[str] | None = None, count: int = 3, constraints: dict | None = None, exclude_product_ids: list[str] | None = None):
    return recommend(tags, category, max_price, exclude_tags, categories, count, constraints, exclude_product_ids)


def recommendation_metadata(constraints: dict | None = None) -> dict:
    return {"results": [], "relaxation_options": relaxation_options(constraints)}
