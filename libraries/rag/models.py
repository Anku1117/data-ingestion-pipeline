from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(BaseModel):
    document_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex}")
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = ""
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chunk_{uuid.uuid4().hex}")
    document_id: str
    content: str
    chunk_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
