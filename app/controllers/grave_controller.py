# app\controllers\grave_controller.py
import uuid
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db.connection import get_session
from app.models.grave_model import Grave
from app.models.informer_model import Informer
from app.models.deleted_grave_model import DeletedGrave
from app.schemas.grave_schema import (
    GraveWithInformerRead,
    GraveInformerDetailRead,
    GraveInformerCreate,
    GraveInformerUpdate,
    DeletedGraveWithInformerRead,
)


def get_graves(session: Session = Depends(get_session)) -> list[Grave]:
    statement = select(Grave).order_by(Grave.created_at.desc())
    return session.exec(statement).all()


def get_graves_with_informers(
    session: Session = Depends(get_session),
) -> list[GraveWithInformerRead]:
    statement = (
        select(Grave, Informer)
        .join(Informer, Grave.id == Informer.grave_id, isouter=True)
        .order_by(Grave.created_at.desc())
    )
    results = session.exec(statement).all()

    combined = []
    for grave, informer in results:
        combined.append(
            GraveWithInformerRead(
                id=grave.id,
                grave_id=grave.grave_id,
                old_grave_id=grave.old_grave_id,
                deceased_name=grave.deceased_name,
                deceased_surname=grave.deceased_surname,
                father_or_husband_name=grave.father_or_husband_name,
                zone_id=grave.zone_id,
                date_of_birth=grave.date_of_birth,
                date_of_death=grave.date_of_death,
                identification_number=grave.identification_number,
                gender=grave.gender,
                native_place=grave.native_place,
                created_at=grave.created_at,
                informer_full_name=informer.informer_full_name if informer else None,
                relationship_with_deceased=informer.relationship_with_deceased if informer else None,
                informer_cnic=informer.informer_cnic if informer else None,
                informer_contact_number=informer.informer_contact_number if informer else None,
                additional_contact_number=informer.additional_contact_number if informer else None,
                informer_city=informer.informer_city if informer else None,
                informer_country=informer.informer_country if informer else None,
                form_received_by=informer.form_received_by if informer else None,
            )
        )
    return combined


def get_grave_with_informer(
    grave_id: uuid.UUID, session: Session = Depends(get_session)
) -> GraveInformerDetailRead:
    grave = session.get(Grave, grave_id)
    if not grave:
        raise HTTPException(status_code=404, detail="Grave not found")

    informer = session.exec(
        select(Informer).where(Informer.grave_id == grave_id)
    ).first()

    return GraveInformerDetailRead(
        id=grave.id,
        grave_id=grave.grave_id,
        old_grave_id=grave.old_grave_id,
        google_map_location=grave.google_map_location,
        zone_id=grave.zone_id,
        deceased_name=grave.deceased_name,
        deceased_surname=grave.deceased_surname,
        father_or_husband_name=grave.father_or_husband_name,
        date_of_birth=grave.date_of_birth,
        date_of_death=grave.date_of_death,
        date_buried=grave.date_buried,
        islamic_date_of_death=grave.islamic_date_of_death,
        identification_type=grave.identification_type,
        identification_number=grave.identification_number,
        gender=grave.gender,
        reason_of_death=grave.reason_of_death,
        neighbor_grave_id_1=grave.neighbor_grave_id_1,
        neighbor_grave_id_2=grave.neighbor_grave_id_2,
        native_place=grave.native_place,
        created_at=grave.created_at,
        updated_at=grave.updated_at,
        informer_id=informer.id if informer else None,
        informer_full_name=informer.informer_full_name if informer else None,
        relationship_with_deceased=informer.relationship_with_deceased if informer else None,
        informer_cnic=informer.informer_cnic if informer else None,
        informer_contact_number=informer.informer_contact_number if informer else None,
        additional_contact_number=informer.additional_contact_number if informer else None,
        informer_address=informer.informer_address if informer else None,
        informer_city=informer.informer_city if informer else None,
        informer_country=informer.informer_country if informer else None,
        form_received_by=informer.form_received_by if informer else None,
    )


def create_grave_with_informer(
    payload: GraveInformerCreate,
    session: Session = Depends(get_session),
) -> GraveInformerDetailRead:
    grave_fields = {
        "grave_id", "old_grave_id", "google_map_location", "zone_id",
        "deceased_name", "deceased_surname", "father_or_husband_name",
        "date_of_birth", "date_of_death", "date_buried",
        "islamic_date_of_death", "identification_type", "identification_number",
        "gender", "reason_of_death", "neighbor_grave_id_1",
        "neighbor_grave_id_2", "native_place",
    }
    informer_fields = {
        "informer_full_name", "relationship_with_deceased", "informer_cnic",
        "informer_contact_number", "additional_contact_number",
        "informer_address", "informer_city", "informer_country",
        "form_received_by",
    }

    data = payload.model_dump(exclude_unset=True)

    grave_data = {k: v for k, v in data.items() if k in grave_fields}
    grave = Grave(**grave_data)
    session.add(grave)

    informer_data = {k: v for k, v in data.items() if k in informer_fields and v is not None}
    if informer_data:
        required = {"informer_full_name", "relationship_with_deceased", "informer_contact_number"}
        missing = required - informer_data.keys()
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create informer, missing required fields: {', '.join(missing)}",
            )

        informer = Informer(grave_id=grave.id, **informer_data)
        session.add(informer)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="A grave with this identification number already exists.",
        )

    return get_grave_with_informer(grave.id, session)


def update_grave_with_informer(
    grave_id: uuid.UUID,
    payload: GraveInformerUpdate,
    session: Session = Depends(get_session),
) -> GraveInformerDetailRead:
    grave = session.get(Grave, grave_id)
    if not grave:
        raise HTTPException(status_code=404, detail="Grave not found")

    grave_fields = {
        "grave_id", "old_grave_id", "google_map_location", "zone_id",
        "deceased_name", "deceased_surname", "father_or_husband_name",
        "date_of_birth", "date_of_death", "date_buried",
        "islamic_date_of_death", "identification_type", "identification_number",
        "gender", "reason_of_death", "neighbor_grave_id_1",
        "neighbor_grave_id_2", "native_place",
    }
    informer_fields = {
        "informer_full_name", "relationship_with_deceased", "informer_cnic",
        "informer_contact_number", "additional_contact_number",
        "informer_address", "informer_city", "informer_country",
        "form_received_by",
    }

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key in grave_fields:
            setattr(grave, key, value)
    grave.updated_at = datetime.utcnow()
    session.add(grave)

    informer_updates = {k: v for k, v in update_data.items() if k in informer_fields}
    if informer_updates:
        informer = session.exec(
            select(Informer).where(Informer.grave_id == grave_id)
        ).first()

        if informer:
            for key, value in informer_updates.items():
                setattr(informer, key, value)
            informer.updated_at = datetime.utcnow()
            session.add(informer)
        else:
            required = {"informer_full_name", "relationship_with_deceased", "informer_contact_number"}
            missing = required - informer_updates.keys()
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot create informer, missing required fields: {', '.join(missing)}",
                )
            informer = Informer(grave_id=grave_id, **informer_updates)
            session.add(informer)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="A grave with this identification number already exists.",
        )

    return get_grave_with_informer(grave_id, session)


def delete_grave(grave_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    """Hard delete — kept for reference/API completeness, no longer called from the UI."""
    grave = session.get(Grave, grave_id)
    if not grave:
        raise HTTPException(status_code=404, detail="Grave not found")

    informers = session.exec(
        select(Informer).where(Informer.grave_id == grave_id)
    ).all()
    for informer in informers:
        informer.grave_id = None
        session.add(informer)

    session.delete(grave)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Could not delete grave: related records still exist.",
        )

    return {"message": "Grave record deleted successfully. Linked informer(s) were kept but unlinked."}


def erase_grave(grave_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    grave = session.get(Grave, grave_id)
    if not grave:
        raise HTTPException(status_code=404, detail="Grave not found")

    deleted_grave = DeletedGrave(**grave.model_dump())
    session.add(deleted_grave)
    session.delete(grave)
    session.commit()

    return {"message": "Grave moved to Deleted Graves. Linked informer remains connected."}


def get_deleted_graves_with_informers(
    session: Session = Depends(get_session),
) -> list[DeletedGraveWithInformerRead]:
    statement = (
        select(DeletedGrave, Informer)
        .join(Informer, DeletedGrave.id == Informer.grave_id, isouter=True)
        .order_by(DeletedGrave.deleted_at.desc())
    )
    results = session.exec(statement).all()

    combined = []
    for grave, informer in results:
        combined.append(
            DeletedGraveWithInformerRead(
                id=grave.id,
                grave_id=grave.grave_id,
                old_grave_id=grave.old_grave_id,
                deceased_name=grave.deceased_name,
                deceased_surname=grave.deceased_surname,
                father_or_husband_name=grave.father_or_husband_name,
                zone_id=grave.zone_id,
                date_of_birth=grave.date_of_birth,
                date_of_death=grave.date_of_death,
                identification_number=grave.identification_number,
                gender=grave.gender,
                native_place=grave.native_place,
                created_at=grave.created_at,
                deleted_at=grave.deleted_at,
                informer_full_name=informer.informer_full_name if informer else None,
                relationship_with_deceased=informer.relationship_with_deceased if informer else None,
                informer_cnic=informer.informer_cnic if informer else None,
                informer_contact_number=informer.informer_contact_number if informer else None,
                additional_contact_number=informer.additional_contact_number if informer else None,
                informer_city=informer.informer_city if informer else None,
                informer_country=informer.informer_country if informer else None,
                form_received_by=informer.form_received_by if informer else None,
            )
        )
    return combined


def restore_grave(grave_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    deleted_grave = session.get(DeletedGrave, grave_id)
    if not deleted_grave:
        raise HTTPException(status_code=404, detail="Deleted grave not found")

    data = deleted_grave.model_dump(exclude={"deleted_at"})
    grave = Grave(**data)
    session.add(grave)
    session.delete(deleted_grave)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot restore: a grave with this identification number already exists.",
        )

    return {"message": "Grave restored successfully."}


def permanent_delete_grave(grave_id: uuid.UUID, session: Session = Depends(get_session)) -> dict:
    deleted_grave = session.get(DeletedGrave, grave_id)
    if not deleted_grave:
        raise HTTPException(status_code=404, detail="Deleted grave not found")

    informers = session.exec(
        select(Informer).where(Informer.grave_id == grave_id)
    ).all()
    for informer in informers:
        informer.grave_id = None
        session.add(informer)

    session.delete(deleted_grave)
    session.commit()

    return {"message": "Grave permanently deleted. Linked informer(s) were unlinked."}