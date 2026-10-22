from hashlib import sha256
from typing import Protocol
import math
from office_agent.config import settings
class EmbeddingProvider(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

class HashEmbeddingProvider:
    """Deterministic offline fallback; production can select sentence-transformers."""
    def __init__(self, dimensions=384): self.dimensions = dimensions
    def _embed(self, text: str) -> list[float]:
        values = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = sha256(token.encode()).digest(); index = int.from_bytes(digest[:4], "big") % self.dimensions
            values[index] += 1.0 if digest[4] % 2 else -1.0
        norm = math.sqrt(sum(x*x for x in values)) or 1
        return [x / norm for x in values]
    async def embed_text(self, text): return self._embed(text)
    async def embed_batch(self, texts): return [self._embed(t) for t in texts]

class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str): self.model_name = model_name; self._model = None
    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
    async def embed_text(self, text): return (await self.embed_batch([text]))[0]
    async def embed_batch(self, texts):
        self._load(); return self._model.encode(texts, normalize_embeddings=True).tolist()

def build_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "sentence_transformers":
        return SentenceTransformerEmbeddingProvider(settings.embedding_model)
    return HashEmbeddingProvider()
