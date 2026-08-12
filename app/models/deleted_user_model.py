# app/models/deleted_user_model.py
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from app.enums.user_enums import UserRole


class DeletedUser(SQLModel, table=True):
    __tablename__ = "deleted_users"

    id: uuid.UUID = Field(primary_key=True)
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None

    role: UserRole = Field(
        sa_column=Column(PGEnum(UserRole, name="user_role", create_type=False)),
        default=UserRole.staff,
    )

    role_id: Optional[uuid.UUID] = Field(default=None)
    is_super_admin: bool = Field(default=False)

    is_active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime = Field(default_factory=datetime.utcnow)