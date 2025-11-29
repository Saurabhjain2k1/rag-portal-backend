from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)  # where file is stored
    status = Column(String(50), default="UPLOADED")  # UPLOADED / PROCESSING / READY / FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", backref="documents")
