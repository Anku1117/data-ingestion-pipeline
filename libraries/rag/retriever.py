from __future__ import annotations

from libraries.logging.logging import get_logger
from libraries.rag.chunker import Chunker
from libraries.rag.models import Document, SearchResult
from libraries.rag.vector_store import DummyEmbeddingProvider, EmbeddingProvider, VectorStore

logger = get_logger(__name__)


class Retriever:
    """RAG retriever: document ingestion and retrieval."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider | None = None,
        chunker: Chunker | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider or DummyEmbeddingProvider()
        self._chunker = chunker or Chunker()

    async def ingest(self, document: Document) -> int:
        chunks = self._chunker.chunk(document)

        embeddings = await self._embedding_provider.embed_batch(
            [c.content for c in chunks]
        )
        for chunk, embedding in zip(chunks, embeddings, strict=False):
            chunk.embedding = embedding

        count = await self._vector_store.add_chunks(chunks)
        logger.info(
            "Document ingested doc_id=%s chunks=%d", document.document_id, count
        )
        return count

    async def retrieve(
        self, query: str, top_k: int = 10
    ) -> list[SearchResult]:
        query_embedding = await self._embedding_provider.embed(query)
        results = await self._vector_store.search(query_embedding, top_k=top_k)
        logger.debug("Retrieved %d results for query", len(results))
        return results

    async def delete_document(self, document_id: str) -> bool:
        return await self._vector_store.delete_document(document_id)
