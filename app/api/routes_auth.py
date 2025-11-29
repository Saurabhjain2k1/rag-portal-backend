# app/api/routes_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    TenantRegisterRequest,
    LoginRequest,
    TokenResponse,
    UserInfo,
    ChangePasswordRequest
)
from app.schemas.tenant import TenantResponse
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-tenant", response_model=TenantResponse)
def register_tenant(
    data: TenantRegisterRequest,
    db: Session = Depends(deps.get_db),
):
    # 1. Check if tenant name exists
    existing_tenant = db.query(Tenant).filter(Tenant.name == data.tenant_name).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant name already exists",
        )

    # 2. Check if user email exists
    existing_user = db.query(User).filter(User.email == data.admin_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # 3. Create tenant
    tenant = Tenant(name=data.tenant_name)
    db.add(tenant)
    db.flush()  # get tenant.id

    # 4. Create admin user for this tenant
    user = User(
        tenant_id=tenant.id,
        email=data.admin_email,
        password_hash=hash_password(data.admin_password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(tenant)

    return tenant


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(deps.get_db),
):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=user.tenant_id,
        role=user.role,
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserInfo)
def get_me(
    current_user: User = Depends(deps.get_current_user),
):
    tenant_name = current_user.tenant.name if current_user.tenant else None
    return UserInfo(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        tenant_name=tenant_name,
        created_at=current_user.created_at,
    )

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Change the password for the currently logged-in user.
    """

    # 1. Verify current password
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Optional: very basic check new != old
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Optional: minimal length check
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long",
        )

    # 2. Update password hash
    current_user.password_hash = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()

    return {"detail": "Password changed successfully"}