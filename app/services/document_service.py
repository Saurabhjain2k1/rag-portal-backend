# app/services/document_service.py
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document


STORAGE_ROOT = Path("storage")


def save_document(
    db: Session,
    tenant_id: int,
    file: UploadFile,
) -> Document:
    """
    1. Create Document row
    2. Save file to disk under storage/<tenant_id>/<document_id>_<filename>
    3. Update storage_path
    """
    # 1. Create DB row with placeholder storage_path
    doc = Document(
        tenant_id=tenant_id,
        filename=file.filename,
        storage_path="",  # will be updated after we know the path
        status="UPLOADED",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 2. Build storage path
    tenant_dir = STORAGE_ROOT / str(tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{doc.id}_{file.filename}"
    file_path = tenant_dir / safe_name

    # 3. Save file contents
    with file_path.open("wb") as f:
        # read in chunks to avoid big memory usage
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    # 4. Update document with final storage_path
    doc.storage_path = str(file_path)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc


def save_url_document(
    db: Session,
    tenant_id: int,
    url: str,
) -> Document:
    """
    Register URL as document source.
    No file is saved; storage_path contains the URL itself.
    """
    doc = Document(
        tenant_id=tenant_id,
        filename=url,         # display URL in UI
        storage_path=url,     # store URL directly
        status="UPLOADED",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
