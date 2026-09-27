from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from libraries.database.session import Base


class PgVectorChunk(Base):
    __tablename__ = "pgvector_chunks"

    chunk_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False, default=0)
    embedding: Mapped[list[float] | None] = mapped_column(nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    embedding_dimension: Mapped[int | None] = mapped_column(
        nullable=True,
        default=1536,
    )
    metadata: Mapped[dict] = mapped_column("metadata", default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda now: datetime.now(UTC),
    )

    __table_args__ = (
        # Index for document_id lookups
        {"postgresql_using": "hash", "postgresql_ops": {"document_id": "text_ops"}},
    )
