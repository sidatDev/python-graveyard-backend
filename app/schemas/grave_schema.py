# app\schemas\grave_schema.py
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

from app.enums.grave_enums import IdentificationType


class GraveRead(BaseModel):
    id: uuid.UUID
    grave_id: Optional[int]
    old_grave_id: Optional[str]
    google_map_location: Optional[str]
    zone_id: Optional[str]
    deceased_name: str
    deceased_surname: Optional[str]
    father_or_husband_name: Optional[str]
    date_of_birth: Optional[date]
    date_of_death: Optional[date]
    date_buried: Optional[date]
    islamic_date_of_death: Optional[str]
    identification_type: Optional[IdentificationType]
    identification_number: Optional[str]
    gender: Optional[str]
    reason_of_death: Optional[str]
    neighbor_grave_id_1: Optional[int]
    neighbor_grave_id_2: Optional[int]
    native_place: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraveWithInformerRead(BaseModel):
    id: uuid.UUID
    # Grave fields
    grave_id: Optional[int]
    old_grave_id: Optional[str]
    deceased_name: str
    deceased_surname: Optional[str]
    father_or_husband_name: Optional[str]
    zone_id: Optional[str]
    date_of_birth: Optional[date]
    date_of_death: Optional[date]
    identification_number: Optional[str]
    gender: Optional[str]
    native_place: Optional[str]
    created_at: datetime

    # Informer fields
    informer_full_name: Optional[str]
    relationship_with_deceased: Optional[str]
    informer_cnic: Optional[str]
    informer_contact_number: Optional[str]
    additional_contact_number: Optional[str]
    informer_city: Optional[str]
    informer_country: Optional[str]
    form_received_by: Optional[str]

    class Config:
        from_attributes = True


class GraveInformerDetailRead(BaseModel):
    id: uuid.UUID
    grave_id: Optional[int]
    old_grave_id: Optional[str]
    google_map_location: Optional[str]
    zone_id: Optional[str]
    deceased_name: str
    deceased_surname: Optional[str]
    father_or_husband_name: Optional[str]
    date_of_birth: Optional[date]
    date_of_death: Optional[date]
    date_buried: Optional[date]
    islamic_date_of_death: Optional[str]
    identification_type: Optional[IdentificationType]
    identification_number: Optional[str]
    gender: Optional[str]
    reason_of_death: Optional[str]
    neighbor_grave_id_1: Optional[int]
    neighbor_grave_id_2: Optional[int]
    native_place: Optional[str]
    created_at: datetime
    updated_at: datetime

    informer_id: Optional[uuid.UUID]
    informer_full_name: Optional[str]
    relationship_with_deceased: Optional[str]
    informer_cnic: Optional[str]
    informer_contact_number: Optional[str]
    additional_contact_number: Optional[str]
    informer_address: Optional[str]
    informer_city: Optional[str]
    informer_country: Optional[str]
    form_received_by: Optional[str]

    class Config:
        from_attributes = True


class GraveInformerUpdate(BaseModel):
    grave_id: Optional[int] = None
    old_grave_id: Optional[str] = None
    google_map_location: Optional[str] = None
    zone_id: Optional[str] = None
    deceased_name: Optional[str] = None
    deceased_surname: Optional[str] = None
    father_or_husband_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    date_buried: Optional[date] = None
    islamic_date_of_death: Optional[str] = None
    identification_type: Optional[IdentificationType] = None
    identification_number: Optional[str] = None
    gender: Optional[str] = None
    reason_of_death: Optional[str] = None
    neighbor_grave_id_1: Optional[int] = None
    neighbor_grave_id_2: Optional[int] = None
    native_place: Optional[str] = None

    informer_full_name: Optional[str] = None
    relationship_with_deceased: Optional[str] = None
    informer_cnic: Optional[str] = None
    informer_contact_number: Optional[str] = None
    additional_contact_number: Optional[str] = None
    informer_address: Optional[str] = None
    informer_city: Optional[str] = None
    informer_country: Optional[str] = None
    form_received_by: Optional[str] = None


class GraveInformerCreate(BaseModel):
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
    identification_type: Optional[IdentificationType] = None
    identification_number: Optional[str] = None
    gender: Optional[str] = None
    reason_of_death: Optional[str] = None
    neighbor_grave_id_1: Optional[int] = None
    neighbor_grave_id_2: Optional[int] = None
    native_place: Optional[str] = None

    informer_full_name: Optional[str] = None
    relationship_with_deceased: Optional[str] = None
    informer_cnic: Optional[str] = None
    informer_contact_number: Optional[str] = None
    additional_contact_number: Optional[str] = None
    informer_address: Optional[str] = None
    informer_city: Optional[str] = None
    informer_country: Optional[str] = None
    form_received_by: Optional[str] = None



class DeletedGraveWithInformerRead(BaseModel):
    id: uuid.UUID
    grave_id: Optional[int]
    old_grave_id: Optional[str]
    deceased_name: str
    deceased_surname: Optional[str]
    father_or_husband_name: Optional[str]
    zone_id: Optional[str]
    date_of_birth: Optional[date]
    date_of_death: Optional[date]
    identification_number: Optional[str]
    gender: Optional[str]
    native_place: Optional[str]
    created_at: datetime
    deleted_at: datetime

    informer_full_name: Optional[str]
    relationship_with_deceased: Optional[str]
    informer_cnic: Optional[str]
    informer_contact_number: Optional[str]
    additional_contact_number: Optional[str]
    informer_city: Optional[str]
    informer_country: Optional[str]
    form_received_by: Optional[str]

    class Config:
        from_attributes = True