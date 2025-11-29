# app/schemas/document.py
from datetime import datetime
from pydantic import BaseModel
from typing import List


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UrlUploadRequest(BaseModel):
    url: str

class PaginatedDocumentsResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    limit: int