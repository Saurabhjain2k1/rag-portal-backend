# app/api/routes_documents.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.ai import get_ai_provider
from app.ai.base import AIProvider
from app.services.ingestion_service import ingest_with_langchain
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse, UrlUploadRequest, PaginatedDocumentsResponse
from app.services.document_service import save_document, save_url_document
# from app.services.url_ingestion_service import ingest_from_url
from app.api import deps
from sqlalchemy.orm import Session
from typing import List
from app.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_FILE_SIZE_BYTES = settings.max_file_size_mb * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.require_admin),  # 👈 admin-only
):
    """
    Upload a document for the current tenant (admin-only).
    """
    # Read file into memory once
    content = await file.read()

    # 🚨 1. Enforce file size limit
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max allowed size is {settings.max_file_size_mb} MB.",
        )

    # 🚨 2. Optional: reject empty files
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file is not allowed.")
    
    doc = save_document(db=db, tenant_id=admin_user.tenant_id, file=file)
    return doc



@router.get("/", response_model=PaginatedDocumentsResponse)
def list_documents(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Paginated documents list.
    Returns:
    {
        "items": [...],
        "total": 123,
        "page": 1,
        "limit": 10
    }
    """
    if page < 1:
        page = 1
    if limit < 1:
        limit = 10

    base_query = db.query(Document).filter(
        Document.tenant_id == current_user.tenant_id
    )

    total = base_query.count()

    docs = (
        base_query
        .order_by(Document.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return PaginatedDocumentsResponse(
        items=docs,
        total=total,
        page=page,
        limit=limit,
    )



@router.post("/{document_id}/ingest")
def ingest_document_endpoint(
    document_id: int,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.require_admin),
):
    doc = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.tenant_id == admin_user.tenant_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found for this tenant",
        )

    try:
        chunk_count = ingest_with_langchain(
            db=db,
            document=doc,
            tenant_id=admin_user.tenant_id,
        )
        doc.status = "READY"
        db.commit()

        return {
            "document_id": doc.id,
            "chunks_indexed": chunk_count,
            "status": "READY",
        }
    except Exception as e:
        doc.status = "FAILED"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        )

@router.post("/upload-url", response_model=DocumentResponse)
def upload_document_url(
    payload: UrlUploadRequest,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.require_admin),
):
    """
    Registers a URL as a document for ingestion (admin-only).
    """
    url = payload.url

    if not url.startswith("http"):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must start with http or https.",
        )

    # Save as a document with storage_path set to the URL
    doc = save_url_document(
        db=db,
        tenant_id=admin_user.tenant_id,
        url=url,
    )

    return doc

