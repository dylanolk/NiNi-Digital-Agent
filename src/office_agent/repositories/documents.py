from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from office_agent.db.models import Document, DocumentChunk
class DocumentRepository:
    def __init__(self, session: Session): self.session = session
    def by_checksum(self, checksum: str) -> Document | None: return self.session.scalar(select(Document).where(Document.checksum == checksum))
    def get(self, document_id: UUID) -> Document | None:
        return self.session.scalar(select(Document).options(joinedload(Document.product)).where(Document.id == document_id))
    def add(self, doc: Document) -> Document: self.session.add(doc); self.session.flush(); return doc
    def for_product(self, product_id: UUID) -> list[Document]:
        return list(self.session.scalars(select(Document).where(Document.product_id == product_id).order_by(Document.created_at.desc())))
    def search_chunks(self, product_ids=None, document_types=None, limit=10) -> list[DocumentChunk]:
        stmt = select(DocumentChunk).join(Document).options(joinedload(DocumentChunk.document).joinedload(Document.product).joinedload(Product.manufacturer))
        if product_ids: stmt = stmt.where(Document.product_id.in_(product_ids))
        if document_types: stmt = stmt.where(Document.document_type.in_(document_types))
        return list(self.session.scalars(stmt.limit(min(limit * 5, 100))).unique())
    def search_chunks_by_embedding(self, embedding, product_ids=None, document_types=None, limit=50) -> list[DocumentChunk]:
        stmt = select(DocumentChunk).join(Document).join(Product).join(Product.manufacturer).options(joinedload(DocumentChunk.document).joinedload(Document.product).joinedload(Product.manufacturer))
        if product_ids: stmt = stmt.where(Document.product_id.in_(product_ids))
        if document_types: stmt = stmt.where(Document.document_type.in_(document_types))
        # pgvector supplies the cosine-distance comparator. SQLite uses the
        # ordinary candidate path because its JSON fallback is not searchable.
        if self.session.bind and self.session.bind.dialect.name == "postgresql":
            stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(embedding)).limit(min(max(limit, 1), 100))
        else:
            stmt = stmt.limit(500)
        return list(self.session.scalars(stmt).unique())
from office_agent.db.models import Product
