import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from xiaosu.core.config import Settings
from xiaosu.db.models import Document, DocumentChunk
from xiaosu.knowledge.chunker import chunk_segments
from xiaosu.knowledge.embeddings import DashScopeEmbeddingClient
from xiaosu.knowledge.parser import parse_document
from xiaosu.knowledge.schemas import Citation


class DocumentNotFoundError(LookupError):
    pass


class EmptyDocumentError(ValueError):
    pass


class DocumentService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def list_documents(self) -> list[Document]:
        result = await self.session.scalars(select(Document).order_by(Document.updated_at.desc()))
        return list(result)

    async def get_document(self, document_id: UUID) -> Document:
        document = await self.session.get(Document, document_id)
        if document is None:
            raise DocumentNotFoundError(str(document_id))
        return document

    async def save_and_index(
        self,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> tuple[str, Document]:
        digest = hashlib.sha256(content).hexdigest()
        existing = await self.session.scalar(select(Document).where(Document.filename == filename))
        if existing is not None and existing.content_hash == digest:
            return "unchanged", existing

        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4().hex}{Path(filename).suffix.lower()}"
        stored_path = self.settings.upload_dir / stored_name
        stored_path.write_bytes(content)

        old_path: Path | None = None
        if existing is None:
            document = Document(
                filename=filename,
                stored_name=stored_name,
                mime_type=content_type,
                content_hash=digest,
                size_bytes=len(content),
            )
            self.session.add(document)
            action = "created"
        else:
            document = existing
            old_path = self.settings.upload_dir / document.stored_name
            document.stored_name = stored_name
            document.mime_type = content_type
            document.content_hash = digest
            document.size_bytes = len(content)
            document.status = "pending"
            document.error_message = None
            document.chunk_count = 0
            document.version += 1
            await self.session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            action = "updated"
        await self.session.commit()
        if old_path is not None and old_path != stored_path:
            old_path.unlink(missing_ok=True)
        await self.index(document)
        return action, document

    async def index(self, document: Document) -> None:
        document.status = "indexing"
        document.error_message = None
        await self.session.commit()
        try:
            path = self.settings.upload_dir / document.stored_name
            segments = parse_document(document.filename, path.read_bytes())
            chunks = chunk_segments(
                segments,
                chunk_size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
            )
            if not chunks:
                raise EmptyDocumentError("文档没有可索引的文本内容")
            embedder = DashScopeEmbeddingClient(self.settings)
            embeddings: list[list[float]] = []
            for start in range(0, len(chunks), 10):
                batch = chunks[start : start + 10]
                embeddings.extend(await embedder.embed([chunk.content for chunk in batch]))
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                self.session.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        section_title=chunk.section_title,
                        page_number=chunk.page_number,
                        paragraph_start=chunk.paragraph_start,
                        paragraph_end=chunk.paragraph_end,
                        content=chunk.content,
                        token_count=max(1, len(chunk.content) // 2),
                        embedding=embedding,
                        chunk_metadata={},
                    )
                )
            document.chunk_count = len(chunks)
            document.status = "indexed"
            await self.session.commit()
        except Exception as error:
            await self.session.rollback()
            current = await self.session.get(Document, document.id)
            if current is not None:
                current.status = "failed"
                current.error_message = str(error)[:2000]
                current.chunk_count = 0
                await self.session.commit()

    async def reindex(self, document_id: UUID) -> Document:
        document = await self.get_document(document_id)
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        await self.session.commit()
        await self.index(document)
        return document

    async def delete(self, document_id: UUID) -> None:
        document = await self.get_document(document_id)
        path = self.settings.upload_dir / document.stored_name
        await self.session.delete(document)
        await self.session.commit()
        path.unlink(missing_ok=True)

    async def list_chunks(self, document_id: UUID) -> list[DocumentChunk]:
        await self.get_document(document_id)
        result = await self.session.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result)

    async def search(self, query: str, limit: int) -> list[Citation]:
        embedder = DashScopeEmbeddingClient(self.settings)
        query_vector = (await embedder.embed([query]))[0]
        distance = DocumentChunk.embedding.cosine_distance(query_vector)
        rows = await self.session.execute(
            select(DocumentChunk, Document, distance.label("distance"))
            .join(Document)
            .options(joinedload(DocumentChunk.document))
            .where(Document.status == "indexed")
            .order_by(distance)
            .limit(min(max(limit, 1), 20))
        )
        return [
            Citation(
                chunk_id=chunk.id,
                document_id=document.id,
                filename=document.filename,
                section_title=chunk.section_title,
                page_number=chunk.page_number,
                paragraph_start=chunk.paragraph_start,
                paragraph_end=chunk.paragraph_end,
                content=chunk.content,
                score=round(max(0.0, 1.0 - float(distance_value)), 4),
            )
            for chunk, document, distance_value in rows
        ]
