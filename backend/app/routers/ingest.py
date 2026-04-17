import asyncio
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.document import KnowledgeDocument, DocumentChunk
from app.schemas.document import KnowledgeDocumentOut, DocumentStatusOut
from app.services.ingest.parser import parse_file
from app.services.ingest.chunker import chunk_text
from app.services.ingest.embedder import embed_chunks, delete_document_embeddings
from app.config import settings

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


async def _process_document(doc_id: str, content: bytes, filename: str, file_type: str):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        doc = await db.get(KnowledgeDocument, doc_id)
        if not doc:
            return
        try:
            doc.status = "processing"
            await db.commit()

            text = parse_file(content, filename)
            chunks = chunk_text(text)

            embed_chunks(chunks, doc_id, filename, file_type)

            chunk_records = [
                DocumentChunk(
                    id=f"{doc_id}_{c.index}",
                    document_id=doc_id,
                    chunk_index=c.index,
                    text_preview=c.text[:200],
                    token_count=c.token_estimate,
                    topic_tag=c.topic_tag,
                )
                for c in chunks
            ]
            db.add_all(chunk_records)
            doc.status = "completed"
            doc.chunk_count = len(chunks)
            await db.commit()

        except Exception as e:
            doc.status = "error"
            doc.error_msg = str(e)[:500]
            await db.commit()


@router.post("/upload", response_model=KnowledgeDocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES and not file.filename.endswith((".pdf", ".txt", ".docx")):
        raise HTTPException(400, "Only PDF, TXT, and DOCX files are supported.")

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb}MB limit.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
    doc_id = str(uuid.uuid4())
    doc = KnowledgeDocument(
        id=doc_id,
        filename=file.filename,
        file_type=ext,
        file_size=len(content),
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(_process_document, doc_id, content, file.filename, ext)
    return doc


@router.get("/documents", response_model=list[KnowledgeDocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
    return result.scalars().all()


@router.get("/documents/{doc_id}/status", response_model=DocumentStatusOut)
async def document_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return DocumentStatusOut(id=doc.id, status=doc.status, chunk_count=doc.chunk_count, error_msg=doc.error_msg)


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    delete_document_embeddings(doc_id)
    await db.delete(doc)
    await db.commit()
