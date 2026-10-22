import asyncio
import json
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from office_agent.db.models import Base
from office_agent.mcp import server
from office_agent.repositories.prices import PriceRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.catalog import CatalogService
from office_agent.services.product_search import ProductSearchService
from office_agent.services.manual_search import ManualSearchService
from office_agent.services.embeddings import HashEmbeddingProvider
from office_agent.services.spreadsheet import SpreadsheetService
from office_agent.repositories.documents import DocumentRepository

def test_mcp_advertises_expected_tools():
    tools = asyncio.run(server.mcp.list_tools())
    assert {tool.name for tool in tools} == {"search_products", "get_product", "search_user_manuals", "generate_recommendations_xlsx", "preview_catalog_import", "commit_catalog_import"}
    schemas = {tool.name: tool.input_schema["properties"] for tool in tools}
    assert {"category", "attributes", "min_price", "max_price"} <= set(schemas["search_products"])
    assert "product_id" in schemas["get_product"] and "query" in schemas["search_user_manuals"]

def test_mcp_search_products_delegates_to_service(monkeypatch):
    engine = create_engine("sqlite://"); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)(); catalog = CatalogService(ProductRepository(session), PriceRepository(session)); product = catalog.add_product("Acme", "AP", "AP-1", "access_point"); catalog.add_price(product.id, "Vendor", "200.00")
    services = (session, ProductSearchService(ProductRepository(session), PriceRepository(session)), ManualSearchService(DocumentRepository(session), HashEmbeddingProvider()), SpreadsheetService(ProductSearchService(ProductRepository(session), PriceRepository(session))))
    monkeypatch.setattr(server, "_services", lambda: services)
    result = asyncio.run(server.mcp.call_tool("search_products", {"category": "access_point"}))
    assert not result.is_error and "AP-1" in json.dumps(result.content, default=str)
