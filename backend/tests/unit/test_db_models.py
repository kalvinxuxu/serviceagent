from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.app.db.base import Base
from backend.app.db.models import Product

def test_database_models_create_and_persist():
    engine=create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Product(id="SKU001", name="原味吐司", category="早餐", price=12, tags=["低糖"]))
        session.commit()
        assert session.get(Product, "SKU001").name == "原味吐司"
