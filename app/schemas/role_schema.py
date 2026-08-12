# app\schemas\role_schema.py
import uuid
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    permissions: Dict[str, Dict[str, bool]]


class RoleRead(BaseModel):
    id: uuid.UUID
    name: str
    permissions: Dict[str, Dict[str, bool]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[Dict[str, Dict[str, bool]]] = None


class RoleReadWithCount(RoleRead):
    user_count: int = 0


class DeletedRoleRead(BaseModel):
    id: uuid.UUID
    name: str
    permissions: Dict[str, Dict[str, bool]]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime

    class Config:
        from_attributes = True