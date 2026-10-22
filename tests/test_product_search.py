from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from office_agent.db.models import Base
from office_agent.repositories.products import ProductRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.services.catalog import CatalogService
from office_agent.services.product_search import ProductSearchService

@pytest.fixture
def search_service():
    engine = create_engine("sqlite://"); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)()
    catalog = CatalogService(ProductRepository(session), PriceRepository(session))
    ap = catalog.add_product("Acme", "Ceiling Wi-Fi Access Point", "AP-100", "access_point", attributes={"poe": True, "ports": 1})
    switch = catalog.add_product("Acme", "24 Port PoE Switch", "SW-24", "network_switch", attributes={"poe": True, "ports": 24})
    display = catalog.add_product("ViewCo", "Conference Display", "VD-55", "display", attributes={"size": 55})
    catalog.add_price(ap.id, "Vendor", "200.00"); catalog.add_price(switch.id, "Vendor", "600.00"); catalog.add_price(display.id, "Vendor", "900.00")
    ProductRepository(session).deactivate(display.id); session.commit()
    return ProductSearchService(ProductRepository(session), PriceRepository(session)), ap, switch, display

def test_category_and_attribute_filters(search_service):
    service, _, _, _ = search_service
    result = service.search(category="network_switch", attributes={"poe": True})
    assert [item["model"] for item in result["results"]] == ["SW-24"]

def test_text_search_checks_product_fields_and_manufacturer(search_service):
    service, _, _, _ = search_service
    assert service.search(query="Wi-Fi")["results"][0]["model"] == "AP-100"
    assert service.search(query="ViewCo")["results"] == []  # inactive by default
    assert service.search(query="ViewCo", active_only=False)["results"][0]["manufacturer"] == "ViewCo"

def test_latest_price_filters_and_limit(search_service):
    service, ap, _, _ = search_service
    # A later price is authoritative for filtering; the old value is retained.
    service.price_service.prices.session.add(__import__("office_agent.db.models", fromlist=["ProductPrice"]).ProductPrice(product_id=ap.id, vendor="Vendor", amount=Decimal("250.00"), currency="USD")); service.price_service.prices.session.commit()
    assert [x["model"] for x in service.search(category="access_point", min_price="240", max_price="260")["results"]] == ["AP-100"]
    with pytest.raises(ValueError): service.search(limit=0)
    with pytest.raises(ValueError): service.search(min_price="bad")

def test_natural_language_category_alias_and_price_filter(search_service):
    service, _, _, _ = search_service
    result = service.search(query="wireless access point", max_price="250")
    assert [item["model"] for item in result["results"]] == ["AP-100"]

def test_get_product_details_and_invalid_id(search_service):
    service, ap, _, _ = search_service
    result = service.get(ap.id)
    assert result["product_id"] == str(ap.id) and "documents" in result and result["price"]["currency"] == "USD"
    with pytest.raises(ValueError, match="Unknown product ID"): service.get("not-a-uuid")
