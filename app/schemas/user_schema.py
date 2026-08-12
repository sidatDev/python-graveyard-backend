# app/schemas/user_schema.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role_id: Optional[uuid.UUID] = None
    is_super_admin: bool = False

    @model_validator(mode="after")
    def check_role_assignment(self):
        if self.is_super_admin and self.role_id:
            raise ValueError("A Super Admin cannot also be assigned a custom role.")
        if not self.is_super_admin and not self.role_id:
            raise ValueError("A role is required unless the user is a Super Admin.")
        return self


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[uuid.UUID] = None
    is_super_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    password: str
    phone: Optional[str]
    role_id: Optional[uuid.UUID]
    is_super_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class DeletedUserRead(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    password: str
    phone: Optional[str]
    role_id: Optional[uuid.UUID]
    is_super_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime

    class Config:
        from_attributes = True