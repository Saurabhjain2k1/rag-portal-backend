# app/schemas/user.py
from datetime import datetime
from typing import Literal, Optional, List

from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["admin", "user"] = "user"


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "user"]] = None
    password: Optional[str] = None  # only if resetting password

class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int