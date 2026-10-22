import asyncio
from pathlib import Path
import fitz
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from office_agent.db.models import Base
from office_agent.repositories.documents import DocumentRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.catalog import CatalogService
from office_agent.services.embeddings import HashEmbeddingProvider
from office_agent.services.manual_ingestion import ManualIngestionService
from office_agent.services.manual_search import ManualSearchService
from office_agent.services.storage import LocalFileStorage

def pdf(path: Path, text: str):
    doc = fitz.open(); page = doc.new_page(); page.insert_text((72, 72), text); path.write_bytes(doc.tobytes()); doc.close()

@pytest.fixture
def manual_search(tmp_path):
    engine = create_engine("sqlite://"); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)(); products = ProductRepository(session); prices = PriceRepository(session)
    catalog = CatalogService(products, prices); ap = catalog.add_product("Acme", "Access Point", "AP-1", "access_point"); switch = catalog.add_product("Acme", "PoE Switch", "SW-1", "network_switch"); other = catalog.add_product("OtherCo", "Camera", "CAM-1", "camera")
    storage = LocalFileStorage(tmp_path / "data"); docs = DocumentRepository(session); ingestion = ManualIngestionService(docs, storage, HashEmbeddingProvider())
    for product, kind, text in [(ap, "user_manual", "Power Requirements. Maximum power consumption: 20W. Power method: IEEE 802.3at PoE+."), (switch, "datasheet", "Power budget. Maximum PoE budget: 200W."), (other, "user_manual", "Camera HDMI output and microphone input.")]:
        path = tmp_path / f"{product.model}.pdf"; pdf(path, text); asyncio.run(ingestion.ingest(product.id, path, kind, source_url=f"https://example.test/{product.model}.pdf"))
    return ManualSearchService(docs, HashEmbeddingProvider()), ap, switch, other

def test_retrieval_returns_technical_evidence_and_provenance(manual_search):
    service, ap, _, _ = manual_search
    result = asyncio.run(service.search("PoE+ maximum power consumption", product_ids=[ap.id]))
    item = result["results"][0]
    assert "20W" in item["content"] and item["page_number"] == 1 and item["document_type"] == "user_manual"
    assert item["source_url"].endswith("AP-1.pdf") and item["product_id"] == str(ap.id)

def test_product_manufacturer_and_document_type_filters(manual_search):
    service, _, switch, other = manual_search
    assert asyncio.run(service.search("PoE budget", product_ids=[switch.id], document_types=["datasheet"]))["results"][0]["model"] == "SW-1"
    assert asyncio.run(service.search("HDMI", manufacturer="OtherCo"))["results"][0]["model"] == "CAM-1"
    acme_results = asyncio.run(service.search("HDMI", manufacturer="Acme"))["results"]
    assert acme_results and all(item["manufacturer"] == "Acme" for item in acme_results)

def test_result_limit_and_required_query(manual_search):
    service, _, _, _ = manual_search
    assert len(asyncio.run(service.search("power", limit=1))["results"]) == 1
    with pytest.raises(ValueError): asyncio.run(service.search("", limit=1))
