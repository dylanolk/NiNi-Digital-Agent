"""Document metadata and original-file storage, independent of the file backend."""
import hashlib
from pathlib import Path
from uuid import UUID
from office_agent.db.models import Document
from office_agent.repositories.documents import DocumentRepository
from office_agent.repositories.products import ProductRepository
from office_agent.services.storage import StorageBackend

class DocumentStorageService:
    def __init__(self, documents: DocumentRepository, products: ProductRepository, storage: StorageBackend):
        self.documents, self.products, self.storage = documents, products, storage

    async def attach_pdf(self, product_id: UUID, content: bytes, filename: str, document_type: str, title: str | None = None, source_url: str | None = None, version: str | None = None):
        if self.products.get(product_id) is None: raise ValueError("Unknown product ID")
        if not content: raise ValueError("Document content cannot be empty")
        if not filename.lower().endswith(".pdf"): raise ValueError("Only PDF documents are supported")
        checksum = hashlib.sha256(content).hexdigest()
        existing = self.documents.by_checksum(checksum)
        if existing is not None: return existing, False
        safe_name = Path(filename).name
        storage_key = f"manuals/{product_id}/{checksum[:12]}-{safe_name}"
        await self.storage.put(storage_key, content)
        document = self.documents.add(Document(product_id=product_id, document_type=document_type, title=title or Path(safe_name).stem, version=version, source_url=source_url, storage_key=storage_key, checksum=checksum))
        self.documents.session.commit()
        return document, True
