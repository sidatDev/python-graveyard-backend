# app\models\informer_model.py
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Informer(SQLModel, table=True):
    __tablename__ = "informers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    grave_id: Optional[uuid.UUID] = Field(default=None, foreign_key="graves.id")
    informer_full_name: str
    relationship_with_deceased: str
    informer_cnic: Optional[str] = None
    informer_contact_number: str
    additional_contact_number: Optional[str] = None
    informer_address: Optional[str] = None
    informer_city: Optional[str] = None
    informer_country: Optional[str] = None
    form_received_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)