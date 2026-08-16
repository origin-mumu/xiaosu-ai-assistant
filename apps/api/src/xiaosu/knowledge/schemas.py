from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    mime_type: str
    content_hash: str
    size_bytes: int
    status: str
    error_message: str | None
    chunk_count: int
    version: int
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    action: Literal["created", "updated", "unchanged"]
    document: DocumentResponse


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    section_title: str | None
    page_number: int | None
    paragraph_start: int | None
    paragraph_end: int | None
    content: str


class OriginalSegmentResponse(BaseModel):
    index: int
    content: str
    section_title: str | None = None
    page_number: int | None = None
    paragraph_number: int | None = None


class DocumentPreviewResponse(BaseModel):
    filename: str
    mime_type: str
    segments: list[OriginalSegmentResponse]


class Citation(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    section_title: str | None = None
    page_number: int | None = None
    paragraph_start: int | None = None
    paragraph_end: int | None = None
    content: str
    score: float


class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: int = 5


class KnowledgeSearchResponse(BaseModel):
    citations: list[Citation]
