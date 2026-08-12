# app\models\role_model.py
import uuid
from datetime import datetime
from typing import Dict, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    permissions: Dict[str, Dict[str, bool]] = Field(
        sa_column=Column(JSONB, nullable=False, server_default="{}")
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DeletedRole(SQLModel, table=True):
    __tablename__ = "deleted_roles"

    id: uuid.UUID = Field(primary_key=True)
    name: str
    permissions: Dict[str, Dict[str, bool]] = Field(
        sa_column=Column(JSONB, nullable=False, server_default="{}")
    )
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime = Field(default_factory=datetime.utcnow)

    # Tracks exactly which users this Erase deactivated, so Restore can
    # reactivate only those users. Not exposed via any response schema.
    deactivated_user_ids: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )