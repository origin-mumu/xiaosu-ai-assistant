from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from xiaosu.api.auth import require_admin
from xiaosu.core.config import Settings, get_settings
from xiaosu.db.session import get_session
from xiaosu.knowledge.parser import SUPPORTED_EXTENSIONS, UnsupportedDocumentError
from xiaosu.knowledge.schemas import (
    ChunkResponse,
    DocumentResponse,
    DocumentUploadResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from xiaosu.knowledge.service import DocumentNotFoundError, DocumentService

router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(require_admin)])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def service(session: SessionDependency, settings: SettingsDependency) -> DocumentService:
    return DocumentService(session, settings)


ServiceDependency = Annotated[DocumentService, Depends(service)]


@router.get("", response_model=list[DocumentResponse])
async def list_documents(document_service: ServiceDependency) -> list[DocumentResponse]:
    documents = await document_service.list_documents()
    return [DocumentResponse.model_validate(document) for document in documents]


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_service: ServiceDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File(description="md/txt/pdf/docx，最大 20 MB")],
) -> DocumentUploadResponse:
    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=422, detail="文件名不能为空")
    if not any(filename.lower().endswith(extension) for extension in SUPPORTED_EXTENSIONS):
        raise HTTPException(status_code=415, detail="仅支持 md、txt、pdf、docx")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="文件超过 20 MB")
    try:
        action, document = await document_service.save_and_index(
            filename,
            file.content_type or "application/octet-stream",
            content,
        )
    except UnsupportedDocumentError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    return DocumentUploadResponse(
        action=action,
        document=DocumentResponse.model_validate(document),
    )


@router.post("/search/query", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    document_service: ServiceDependency,
) -> KnowledgeSearchResponse:
    citations = await document_service.search(request.query, request.limit)
    return KnowledgeSearchResponse(citations=citations)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    document_service: ServiceDependency,
) -> DocumentResponse:
    try:
        document = await document_service.get_document(document_id)
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail="文档不存在") from error
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
async def list_document_chunks(
    document_id: UUID,
    document_service: ServiceDependency,
) -> list[ChunkResponse]:
    try:
        chunks = await document_service.list_chunks(document_id)
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail="文档不存在") from error
    return [ChunkResponse.model_validate(chunk) for chunk in chunks]


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    document_id: UUID,
    document_service: ServiceDependency,
) -> DocumentResponse:
    try:
        document = await document_service.reindex(document_id)
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail="文档不存在") from error
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    document_service: ServiceDependency,
) -> None:
    try:
        await document_service.delete(document_id)
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail="文档不存在") from error
