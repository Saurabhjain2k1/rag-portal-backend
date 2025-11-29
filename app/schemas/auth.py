from pydantic import BaseModel, EmailStr
from typing import Optional

class TenantRegisterRequest(BaseModel):
    tenant_name: str
    admin_email: EmailStr
    admin_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserInfo(BaseModel):
    id: int
    tenant_id: int
    email: EmailStr
    role: str
    tenant_name: Optional[str] = None 
    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
