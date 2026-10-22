import hashlib, re
from pathlib import Path
from datetime import datetime, timezone
from uuid import UUID
import fitz
from office_agent.db.models import Document, DocumentChunk
from office_agent.repositories.documents import DocumentRepository
from office_agent.services.embeddings import EmbeddingProvider
from office_agent.services.storage import StorageBackend

class ManualIngestionService:
    def __init__(self, documents: DocumentRepository, storage: StorageBackend, embeddings: EmbeddingProvider): self.documents, self.storage, self.embeddings = documents, storage, embeddings
    async def ingest(self, product_id: UUID, file_path: str | Path, document_type: str, title: str | None = None, source_url: str | None = None, version: str | None = None):
        path = Path(file_path); raw = path.read_bytes(); checksum = hashlib.sha256(raw).hexdigest()
        existing = self.documents.by_checksum(checksum)
        if existing is not None: return existing, False
        pdf = fitz.open(stream=raw, filetype="pdf")
        pages = [(i + 1, p.get_text("text").strip()) for i,p in enumerate(pdf)]
        pdf.close()
        text = "\n".join(t for _,t in pages)
        if len(text.strip()) < 20: raise ValueError("Manual has no extractable text")
        key = f"manuals/{product_id}/{checksum[:12]}-{path.name}"
        await self.storage.put(key, raw)
        doc = self.documents.add(Document(product_id=product_id, document_type=document_type, title=title or path.stem, version=version, source_url=source_url, storage_key=key, checksum=checksum))
        chunks_text = []
        for page, content in pages:
            words = content.split(); size, overlap = 700, 100
            for start in range(0, len(words), size-overlap):
                chunk = " ".join(words[start:start+size])
                if chunk: chunks_text.append((page, chunk))
        vectors = await self.embeddings.embed_batch([c for _,c in chunks_text])
        for index, ((page, content), embedding) in enumerate(zip(chunks_text, vectors)):
            self.documents.session.add(DocumentChunk(document_id=doc.id, chunk_index=index, page_number=page, section=None, content=content, embedding=embedding))
        self.documents.session.commit(); return doc, True
