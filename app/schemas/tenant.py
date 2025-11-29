# app/schemas/tenant.py
from pydantic import BaseModel


class TenantResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
