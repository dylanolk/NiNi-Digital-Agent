import asyncio
from pathlib import Path
import fitz
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from office_agent.db.models import Base, DocumentChunk
from office_agent.repositories.documents import DocumentRepository
from office_agent.repositories.prices import PriceRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.catalog import CatalogService
from office_agent.services.embeddings import HashEmbeddingProvider
from office_agent.services.manual_ingestion import ManualIngestionService
from office_agent.services.storage import LocalFileStorage

def make_pdf(path: Path, pages: list[str]) -> bytes:
    pdf = fitz.open()
    for text in pages:
        page = pdf.new_page(); page.insert_text((72, 72), text)
    content = pdf.tobytes(); pdf.close(); path.write_bytes(content); return content

@pytest.fixture
def ingestion(tmp_path):
    engine = create_engine("sqlite://"); Base.metadata.create_all(engine); session = sessionmaker(bind=engine)()
    products = ProductRepository(session); product = CatalogService(products, PriceRepository(session)).add_product("Acme", "Demo AP", "AP-1", "access_point")
    service = ManualIngestionService(DocumentRepository(session), LocalFileStorage(tmp_path / "data"), HashEmbeddingProvider())
    return session, product, service, tmp_path

def test_pdf_is_extracted_chunked_embedded_and_deduplicated(ingestion):
    session, product, service, tmp_path = ingestion
    path = tmp_path / "manual.pdf"; content = make_pdf(path, ["Power Requirements\nMaximum power consumption: 20W. Power method: IEEE 802.3at PoE+.", "Installation\nMount on a ceiling with the included bracket."])
    document, created = asyncio.run(service.ingest(product.id, path, "installation_guide", source_url="https://example.test/manual.pdf"))
    assert created and asyncio.run(service.storage.exists(document.storage_key))
    chunks = list(session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)))
    assert len(chunks) == 2 and {chunk.page_number for chunk in chunks} == {1, 2}
    assert len(chunks[0].embedding) == 384 and "20W" in " ".join(chunk.content for chunk in chunks)
    duplicate, duplicate_created = asyncio.run(service.ingest(product.id, path, "installation_guide"))
    assert duplicate.id == document.id and not duplicate_created

def test_image_only_or_empty_pdf_fails_cleanly(ingestion):
    session, product, service, tmp_path = ingestion
    empty = tmp_path / "empty.pdf"; make_pdf(empty, [""])
    with pytest.raises(ValueError, match="extractable text"):
        asyncio.run(service.ingest(product.id, empty, "user_manual"))
