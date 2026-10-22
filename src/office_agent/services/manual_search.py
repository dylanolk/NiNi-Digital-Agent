import re
from uuid import UUID
from office_agent.repositories.documents import DocumentRepository
from office_agent.services.embeddings import EmbeddingProvider
class ManualSearchService:
    def __init__(self, documents: DocumentRepository, embeddings: EmbeddingProvider): self.documents, self.embeddings = documents, embeddings
    async def search(self, query: str, product_ids=None, manufacturer=None, document_types=None, limit=10):
        if not query or not query.strip(): raise ValueError("Query is required")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50: raise ValueError("Limit must be an integer between 1 and 50")
        q = set(re.findall(r"[\w.+-]+", query.lower())); query_vector = await self.embeddings.embed_text(query)
        chunks = self.documents.search_chunks_by_embedding([float(x) for x in query_vector], [UUID(str(x)) for x in product_ids] if product_ids else None, document_types, max(limit * 5, 20))
        scored = []
        for c in chunks:
            d, p = c.document, c.document.product
            if manufacturer and manufacturer.lower() not in p.manufacturer.name.lower(): continue
            words = set(re.findall(r"[\w.+-]+", c.content.lower())); lexical = len(q & words) / max(len(q), 1)
            vector_score = sum(a*b for a,b in zip(query_vector, c.embedding or []))
            scored.append((0.6 * vector_score + 0.4 * lexical, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return {"results": [{"product_id": str(c.document.product_id), "manufacturer": c.document.product.manufacturer.name, "product_name": c.document.product.name, "model": c.document.product.model, "document_id": str(c.document.id), "document_title": c.document.title, "document_type": c.document.document_type, "page_number": c.page_number, "section": c.section, "content": c.content, "source_url": c.document.source_url, "relevance": round(float(score), 5)} for score,c in scored[:min(limit,50)]]}
