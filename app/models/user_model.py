# app/models/user_model.py
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from app.enums.user_enums import UserRole


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None

    # Legacy column — no longer read by the API, kept only so the existing
    # NOT NULL constraint in the database keeps being satisfied automatically.
    role: UserRole = Field(
        sa_column=Column(PGEnum(UserRole, name="user_role", create_type=False)),
        default=UserRole.staff,
    )

    # New dynamic role system
    role_id: Optional[uuid.UUID] = Field(default=None)
    is_super_admin: bool = Field(default=False)

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)