from __future__ import annotations

from libraries.rag.models import Document, DocumentChunk


class Chunker:
    """Splits documents into chunks for embedding."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, document: Document) -> list[DocumentChunk]:
        content = document.content
        chunks: list[DocumentChunk] = []
        start = 0
        index = 0

        while start < len(content):
            end = start + self._chunk_size
            chunk_content = content[start:end]

            chunk = DocumentChunk(
                document_id=document.document_id,
                content=chunk_content,
                chunk_index=index,
                metadata={**document.metadata, "source": document.source},
            )
            chunks.append(chunk)
            start += self._chunk_size - self._chunk_overlap
            index += 1

        return chunks
