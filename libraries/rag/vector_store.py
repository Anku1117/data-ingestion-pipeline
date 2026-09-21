from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from libraries.logging.logging import get_logger
from libraries.rag.models import DocumentChunk, SearchResult

logger = get_logger(__name__)


class VectorStore(ABC):
    """Abstract vector store for document embeddings."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def add_chunks(self, chunks: list[DocumentChunk]) -> int: ...

    @abstractmethod
    async def search(self, query_embedding: list[float], top_k: int = 10) -> list[SearchResult]: ...

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool: ...

    @abstractmethod
    async def health_check(self) -> bool: ...


class MemoryVectorStore(VectorStore):
    """In-memory vector store for development and testing."""

    def __init__(self) -> None:
        self._chunks: dict[str, DocumentChunk] = {}
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("MemoryVectorStore started")

    async def stop(self) -> None:
        self._running = False

    async def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        for chunk in chunks:
            if chunk.embedding is None:
                chunk.embedding = self._dummy_embed(chunk.content)
            self._chunks[chunk.chunk_id] = chunk
        return len(chunks)

    async def search(self, query_embedding: list[float], top_k: int = 10) -> list[SearchResult]:
        results: list[SearchResult] = []
        for chunk in self._chunks.values():
            if chunk.embedding is not None:
                score = self._cosine_similarity(query_embedding, chunk.embedding)
                results.append(
                    SearchResult(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        content=chunk.content,
                        score=score,
                        metadata=chunk.metadata,
                    )
                )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def delete_document(self, document_id: str) -> bool:
        to_delete = [cid for cid, c in self._chunks.items() if c.document_id == document_id]
        for cid in to_delete:
            del self._chunks[cid]
        return len(to_delete) > 0

    async def health_check(self) -> bool:
        return self._running

    def _dummy_embed(self, text: str) -> list[float]:
        h = hashlib.md5(text.encode()).hexdigest()
        return [float(int(h[i : i + 2], 16)) / 255.0 for i in range(0, min(32, len(h)), 2)]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            min_len = min(len(a), len(b))
            a, b = a[:min_len], b[:min_len]
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class DummyEmbeddingProvider(EmbeddingProvider):
    """Deterministic dummy embeddings for testing."""

    async def embed(self, text: str) -> list[float]:
        h = hashlib.md5(text.encode()).hexdigest()
        return [float(int(h[i : i + 2], 16)) / 255.0 for i in range(0, min(32, len(h)), 2)]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]
