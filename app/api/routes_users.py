# app/api/routes_users.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest, UserListResponse
from app.services.auth_service import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.require_admin),
):
    """
    Create a new user in the same tenant as the admin.
    """
    # Check if email already exists (global unique)
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    new_user = User(
        tenant_id=admin_user.tenant_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# @router.get("/", response_model=List[UserResponse])
# def list_users(
#     db: Session = Depends(deps.get_db),
#     admin_user: User = Depends(deps.require_admin),
# ):
#     """
#     List all users within the admin's tenant.
#     """
#     users = (
#         db.query(User)
#         .filter(User.tenant_id == admin_user.tenant_id)
#         .order_by(User.created_at.desc())
#         .all()
#     )
#     return users

# @router.get("/", response_model=List[UserResponse])
# def list_users(
#     skip: int = 0,
#     limit: int = 10,
#     search: str | None = None,
#     db: Session = Depends(deps.get_db),
#     admin_user: User = Depends(deps.require_admin),
# ):
#     """
#     Paginated + searchable user listing.
#     """
#     query = db.query(User).filter(User.tenant_id == admin_user.tenant_id)

#     if search:
#         search = f"%{search.lower()}%"
#         query = query.filter(User.email.ilike(search))

#     users = (
#         query.order_by(User.created_at.desc())
#         .offset(skip)
#         .limit(limit)
#         .all()
#     )
#     return users

@router.get("/", response_model=UserListResponse)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.require_admin),
):
    """
    Paginated + searchable list of users within the admin's tenant.
    """
    base_query = db.query(User).filter(User.tenant_id == admin_user.tenant_id)

    if search:
        pattern = f"%{search.lower()}%"
        base_query = base_query.filter(func.lower(User.email).like(pattern))

    total = base_query.count()

    users = (
        base_query
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return UserListResponse(items=users, total=total)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.require_admin),
):
    """
    Delete a user within the same tenant.
    Prevent admins from deleting themselves (optional).
    """
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.tenant_id == admin_user.tenant_id,
        )
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this tenant",
        )

    # Optional: prevent deleting self
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot delete themselves",
        )

    db.delete(user)
    db.commit()

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.require_admin),
):
    """
    Update email, role, or password of a user in the same tenant.
    """

    user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == admin_user.tenant_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Admin cannot update themselves to user
    if user.id == admin_user.id and payload.role == "user":
        raise HTTPException(
            status_code=400,
            detail="You cannot downgrade your own role"
        )

    # Email update
    if payload.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing and existing.id != user.id:
            raise HTTPException(400, detail="Email already in use")
        user.email = payload.email

    # Role update
    if payload.role:
        if payload.role not in ["admin", "user"]:
            raise HTTPException(400, detail="Invalid role")
        user.role = payload.role

    # Reset Password
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)

    return user