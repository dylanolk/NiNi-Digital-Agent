from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from office_agent.db.models import Base, ProductPrice
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.services.catalog import CatalogService
from office_agent.services.product_search import ProductSearchService

@pytest.fixture
def catalog():
    engine = create_engine("sqlite://"); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)()
    return session, CatalogService(ProductRepository(session), PriceRepository(session))

def test_product_creation_and_deactivation(catalog):
    session, service = catalog
    product = service.add_product("Acme", "Office AP", "AP-1", "access_point", sku="SKU-1", attributes='{"poe": true}')
    assert product.manufacturer.name == "Acme" and product.attributes["poe"] is True
    ProductRepository(session).deactivate(product.id); session.commit()
    assert ProductSearchService(ProductRepository(session), PriceRepository(session)).search()["results"] == []

def test_price_history_and_latest(catalog):
    session, service = catalog
    product = service.add_product("Acme", "Office AP", "AP-1", "access_point")
    old = service.add_price(product.id, "Vendor", "199.995")
    new = service.add_price(product.id, "Vendor", Decimal("215.00"))
    repo = PriceRepository(session)
    assert len(repo.history(product.id)) == 2
    assert repo.latest(product.id).id == new.id
    assert repo.latest(product.id).amount == Decimal("215.00")
    assert old.id != new.id

def test_duplicate_model_and_sku_rejected(catalog):
    _, service = catalog; service.add_product("Acme", "One", "X", "display", sku="S")
    with pytest.raises(Exception): service.add_product("Acme", "Two", "X", "display")
    # Flush failures leave the transaction in a failed state until rolled back.
    service.products.session.rollback()
    with pytest.raises(Exception): service.add_product("Acme", "Three", "Y", "display", sku="S")
