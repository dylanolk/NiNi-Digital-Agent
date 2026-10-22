import asyncio
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from office_agent.db.models import Base
from office_agent.repositories.documents import DocumentRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.catalog import CatalogService
from office_agent.services.document_storage import DocumentStorageService
from office_agent.services.storage import LocalFileStorage

def test_pdf_storage_metadata_and_deduplication(tmp_path):
    engine = create_engine("sqlite://"); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)()
    products = ProductRepository(session); product = CatalogService(products, PriceRepository(session)).add_product("Acme", "Manual AP", "AP-1", "access_point")
    storage = LocalFileStorage(tmp_path); service = DocumentStorageService(DocumentRepository(session), products, storage)
    content = b"%PDF-1.7 synthetic manual content"
    document, created = asyncio.run(service.attach_pdf(product.id, content, "guide.pdf", "installation_guide", source_url="https://example.test/guide.pdf"))
    assert created and document.storage_key.startswith(f"manuals/{product.id}/")
    assert asyncio.run(storage.exists(document.storage_key))
    assert asyncio.run(storage.get(document.storage_key)) == content
    duplicate, created_again = asyncio.run(service.attach_pdf(product.id, content, "renamed.pdf", "installation_guide"))
    assert not created_again and duplicate.id == document.id
    stored = DocumentRepository(session).get(document.id)
    assert stored.source_url == "https://example.test/guide.pdf"

def test_storage_rejects_invalid_input(tmp_path):
    engine = create_engine("sqlite://"); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)(); products = ProductRepository(session)
    product = CatalogService(products, PriceRepository(session)).add_product("Acme", "Manual AP", "AP-1", "access_point")
    service = DocumentStorageService(DocumentRepository(session), products, LocalFileStorage(tmp_path))
    import pytest
    with pytest.raises(ValueError, match="PDF"):
        asyncio.run(service.attach_pdf(product.id, b"data", "guide.txt", "manual"))
