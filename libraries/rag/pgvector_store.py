from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from libraries.rag.models import DocumentChunk, SearchResult
from libraries.database.pyvector_models import PgVectorChunk
from libraries.logging.logging import get_logger
from libraries.rag.vector_store import VectorStore, MemoryVectorStore

logger = get_logger(__name__)


class PgVectorStore(VectorStore):
    """PostgreSQL-backed vector store using pgvector extension.

    Uses pgvector's native cosine distance when available,
    falls back to Python-side computation when pgvector is not installed.
    """

    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory
        self._using_native: bool | None = None

    async def start(self) -> None:
        # Check if pgvector is available
        async with self._session_factory() as session:
            try:
                # Try a pgvector-specific operation
                result = await session.exec("SELECT 1::vector")
                self._using_native = True
                logger.info("PgVectorStore using native pgvector")
            except Exception:
                self._using_native = False
                logger.info("PgVectorStore falling back to Python-side similarity")

    async def stop(self) -> None:
        pass

    async def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        async with self._session_factory() as session:
            for chunk in chunks:
                db_chunk = PgVectorChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    embedding=chunk.embedding,
                    embedding_model=chunk.embedding_model,
                    embedding_dimension=chunk.embedding_dimension,
                    metadata=chunk.metadata,
                )
                session.add(db_chunk)
            await session.flush()
            logger.info("Added %d chunks to PgVectorStore", len(chunks))
            return len(chunks)

    async def search(self, query_embedding: list[float], top_k: int = 10) -> list[SearchResult]:
        async with self._session_factory() as session:
            if self._using_native:
                # Use pgvector native cosine distance
                result = await session.exec(
                    """
                    SELECT 
                        chunk_id,
                        document_id,
                        content,
                        1 - (embedding <=> :query_embedding) AS score,
                        metadata
                    FROM pgvector_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :top_k
                    """
                )
                rows = result.all()
                return [
                    SearchResult(
                        chunk_id=str(row.chunk_id),
                        document_id=row.document_id,
                        content=row.content,
                        score=float(row.score),
                        metadata=row.metadata or {},
                    )
                    for row in rows
                ]
            else:
                # Fall back: load all chunks with embeddings and compute in Python
                result = await session.exec(
                    "SELECT chunk_id, document_id, content, embedding, metadata FROM pgvector_chunks WHERE embedding IS NOT NULL"
                )
                rows = result.all()

                if not rows:
                    return []

                # Compute cosine similarity in Python
                scored: list[tuple[float, SearchResult]] = []
                for row in rows:
                    chunk_embedding = row.embedding
                    if chunk_embedding is None:
                        continue
                    similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                    scored.append(
                        (
                            similarity,
                            SearchResult(
                                chunk_id=str(row.chunk_id),
                                document_id=row.document_id,
                                content=row.content,
                                score=similarity,
                                metadata=row.metadata or {},
                            ),
                        )
                    )

                scored.sort(key=lambda x: x[0], reverse=True)
                return [s[1] for s in scored[:top_k]]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            min_len = min(len(a), len(b))
            a, b = a[:min_len], b[:min_len]
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def delete_document(self, document_id: str) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                "DELETE FROM pgvector_chunks WHERE document_id = :doc_id",
                {"doc_id": document_id},
            )
            deleted = result.rowcount > 0
            await session.flush()
            if deleted:
                logger.info("Deleted chunks for document %s", document_id)
            return deleted

    async def health_check(self) -> bool:
        try:
            async with self._session_factory() as session:
                await session.exec("SELECT 1")
            return True
        except Exception:
            return False
