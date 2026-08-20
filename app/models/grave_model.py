# app\models\grave_model.py
import uuid
from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from app.enums.grave_enums import IdentificationType


class Grave(SQLModel, table=True):
    __tablename__ = "graves"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    grave_id: Optional[int] = None
    old_grave_id: Optional[str] = None
    google_map_location: Optional[str] = None
    zone_id: Optional[str] = None
    deceased_name: str
    deceased_surname: Optional[str] = None
    father_or_husband_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    date_buried: Optional[date] = None
    islamic_date_of_death: Optional[str] = None
    identification_type: Optional[IdentificationType] = Field(
        sa_column=Column(PGEnum(IdentificationType, name="identification_type", create_type=False)),
        default=None,
    )
    identification_number: Optional[str] = Field(default=None, sa_column_kwargs={"unique": True})
    gender: Optional[str] = None
    reason_of_death: Optional[str] = None
    neighbor_grave_id_1: Optional[int] = None
    neighbor_grave_id_2: Optional[int] = None
    native_place: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)