# app/controllers/user_controller.py
import uuid
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlmodel import Session, select

from app.db.connection import get_session
from app.models.user_model import User
from app.models.deleted_user_model import DeletedUser
from app.models.role_model import Role
from app.schemas.user_schema import UserCreate, UserUpdate


def create_user(user_in: UserCreate, session: Session = Depends(get_session)) -> User:
    existing = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_in.role_id:
        role = session.get(Role, user_in.role_id)
        if not role:
            raise HTTPException(status_code=400, detail="Selected role does not exist")

    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password=user_in.password,
        phone=user_in.phone,
        role_id=user_in.role_id,
        is_super_admin=user_in.is_super_admin,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_users(session: Session = Depends(get_session)) -> list[User]:
    return session.exec(select(User)).all()


def get_user(user_id: uuid.UUID, session: Session = Depends(get_session)) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user(
    user_id: uuid.UUID, user_in: UserUpdate, session: Session = Depends(get_session)
) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)

    # A Super Admin bypasses the role system entirely — clear any role_id
    if update_data.get("is_super_admin") is True:
        update_data["role_id"] = None

    if update_data.get("role_id"):
        role = session.get(Role, update_data["role_id"])
        if not role:
            raise HTTPException(status_code=400, detail="Selected role does not exist")

    for key, value in update_data.items():
        setattr(user, key, value)
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(user_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    """Hard delete — kept for reference/API completeness, no longer called from the UI."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()
    return {"message": "User deleted successfully"}


def erase_user(user_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = user.model_dump()
    data["is_active"] = False

    deleted_user = DeletedUser(**data)
    session.add(deleted_user)
    session.delete(user)
    session.commit()

    return {"message": "User moved to Deleted Users."}


def get_deleted_users(session: Session = Depends(get_session)) -> list[DeletedUser]:
    statement = select(DeletedUser).order_by(DeletedUser.deleted_at.desc())
    return session.exec(statement).all()


def restore_user(user_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    deleted_user = session.get(DeletedUser, user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="Deleted user not found")

    existing = session.exec(select(User).where(User.email == deleted_user.email)).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Cannot restore: a user with this email already exists.",
        )

    data = deleted_user.model_dump(exclude={"deleted_at"})
    data["is_active"] = True

    user = User(**data)
    session.add(user)
    session.delete(deleted_user)
    session.commit()

    return {"message": "User restored successfully."}


def permanent_delete_user(user_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    deleted_user = session.get(DeletedUser, user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="Deleted user not found")

    session.delete(deleted_user)
    session.commit()

    return {"message": "User permanently deleted."}