import uuid
from datetime import datetime, date as date_type
from typing import Optional
from fastapi import HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy import func, cast, String
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
    GravePaginatedRead,
    GraveWithInformerPaginatedRead,
)


def get_graves(session: Session = Depends(get_session)) -> list[Grave]:
    statement = select(Grave).order_by(Grave.created_at.desc())
    return session.exec(statement).all()


# Fields the public search is allowed to filter on. Keeping this as an
# explicit whitelist (rather than trusting a raw column name from the
# querystring) avoids exposing arbitrary columns to search/enumeration.
SEARCHABLE_FIELDS = {
    "deceased_name": Grave.deceased_name,
    "deceased_surname": Grave.deceased_surname,
    "father_or_husband_name": Grave.father_or_husband_name,
    "gender": Grave.gender,
    "date_of_death": Grave.date_of_death,
}


def search_graves(
    search_field: Optional[str] = None,
    search_term: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
) -> GravePaginatedRead:
    """
    Public, paginated grave search.

    - Only returns graves that actually have a deceased_name (guards against
      any future blank/placeholder rows), regardless of grave_id/old_grave_id.
    - search_field/search_term are optional together: if provided, both must
      be provided. search_field must be one of SEARCHABLE_FIELDS.
    - date_of_death search_term must be an ISO date string (YYYY-MM-DD),
      matching the <input type="date"> the frontend sends.
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size must be between 1 and 100")

    conditions = [Grave.deceased_name.is_not(None), Grave.deceased_name != ""]

    if search_field is not None or search_term is not None:
        if not search_field or not search_term:
            raise HTTPException(
                status_code=400,
                detail="search_field and search_term must be provided together",
            )
        if search_field not in SEARCHABLE_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid search_field. Must be one of: {', '.join(SEARCHABLE_FIELDS)}",
            )

        column = SEARCHABLE_FIELDS[search_field]

        if search_field == "date_of_death":
            try:
                parsed_date = date_type.fromisoformat(search_term)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="date_of_death search_term must be in YYYY-MM-DD format",
                )
            conditions.append(column == parsed_date)
        else:
            conditions.append(column.ilike(f"%{search_term}%"))

    count_statement = select(func.count()).select_from(Grave).where(*conditions)
    total = session.exec(count_statement).one()

    statement = (
        select(Grave)
        .where(*conditions)
        .order_by(Grave.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = session.exec(statement).all()

    total_pages = (total + page_size - 1) // page_size if total else 0

    return GravePaginatedRead(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# Fields the PUBLIC suggestion dropdown supports - same values as the admin
# SUGGESTION_FIELDS below, kept as a separate constant since the two search
# domains (public vs admin) are intentionally decoupled.
PUBLIC_SUGGESTION_FIELDS = {"deceased_name", "deceased_surname"}


def get_public_grave_search_suggestions(
    search_field: str,
    search_term: str,
    limit: int = 8,
    session: Session = Depends(get_session),
) -> list[str]:
    """
    Type-ahead suggestions for the public grave search box. Same shape as
    the admin version, but queries the plain Grave table (no Informer join)
    and applies the same "has a real deceased_name" visibility rule as
    search_graves(), so suggestions never surface a name that the actual
    search wouldn't also be able to find.
    """
    term = search_term.strip()
    if search_field not in PUBLIC_SUGGESTION_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"search_field must be one of: {', '.join(PUBLIC_SUGGESTION_FIELDS)}",
        )
    if len(term) < 2:
        raise HTTPException(status_code=400, detail="search_term must be at least 2 characters")
    if limit < 1 or limit > 10:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 10")

    term_pattern = f"%{term}%"
    visible = [Grave.deceased_name.is_not(None), Grave.deceased_name != ""]

    if search_field == "deceased_name":
        combined_name = func.concat(
            Grave.deceased_name, " ", func.coalesce(Grave.deceased_surname, "")
        )
        statement = (
            select(combined_name)
            .where(*visible, combined_name.ilike(term_pattern))
            .distinct()
            .order_by(combined_name)
            .limit(limit)
        )
    else:  # deceased_surname
        statement = (
            select(Grave.deceased_surname)
            .where(*visible, Grave.deceased_surname.is_not(None), Grave.deceased_surname.ilike(term_pattern))
            .distinct()
            .order_by(Grave.deceased_surname)
            .limit(limit)
        )

    results = session.exec(statement).all()
    return [value for value in results if value]


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
                date_buried=grave.date_buried,
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


# Fields the admin "View Graves" search bar can filter on. Kept as an
# explicit whitelist for the same reason as SEARCHABLE_FIELDS above.
# "deceased_name" here matches the frontend's getFieldValue(), which
# searches the combined "First Last" string (name + surname together).
ADMIN_SEARCH_FIELDS = {
    "deceased_name",
    "deceased_surname",
    "father_or_husband_name",
    "gender",
    "identification_number",
    "date_of_death",
    "date_buried",
    "grave_id",
    "zone_id",
    "informer_full_name",
    "informer_cnic",
}

# Date fields that accept a range (search_term = from, search_term_to = to)
# instead of a single exact-match value.
ADMIN_DATE_RANGE_FIELDS = {
    "date_of_death": Grave.date_of_death,
    "date_buried": Grave.date_buried,
}


def _parse_search_date(field_name: str, value: str, param_name: str) -> date_type:
    try:
        return date_type.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} {param_name} must be in YYYY-MM-DD format",
        )


def _build_admin_search_condition(
    search_field: str, search_term: str, search_term_to: Optional[str] = None
):
    """Returns a single SQLAlchemy filter condition for one admin search field."""
    term_pattern = f"%{search_term}%"

    if search_field == "deceased_name":
        combined_name = func.concat(
            Grave.deceased_name, " ", func.coalesce(Grave.deceased_surname, "")
        )
        return combined_name.ilike(term_pattern)
    if search_field == "deceased_surname":
        return Grave.deceased_surname.ilike(term_pattern)
    if search_field == "father_or_husband_name":
        return Grave.father_or_husband_name.ilike(term_pattern)
    if search_field == "gender":
        return Grave.gender.ilike(term_pattern)
    if search_field == "identification_number":
        return Grave.identification_number.ilike(term_pattern)
    if search_field == "zone_id":
        return Grave.zone_id.ilike(term_pattern)
    if search_field == "grave_id":
        # grave_id is an integer column, but the frontend does a substring
        # match on its string form (e.g. "20" matches 2001, 2201, ...) -
        # cast to text to replicate that behavior server-side.
        return cast(Grave.grave_id, String).ilike(term_pattern)
    if search_field in ADMIN_DATE_RANGE_FIELDS:
        column = ADMIN_DATE_RANGE_FIELDS[search_field]
        start_date = _parse_search_date(search_field, search_term, "search_term")
        if search_term_to:
            end_date = _parse_search_date(search_field, search_term_to, "search_term_to")
            if end_date < start_date:
                raise HTTPException(
                    status_code=400,
                    detail="search_term_to must be on or after search_term",
                )
            return column.between(start_date, end_date)
        # No "to" date provided - fall back to a single exact-date match.
        return column == start_date
    if search_field == "informer_full_name":
        return Informer.informer_full_name.ilike(term_pattern)
    if search_field == "informer_cnic":
        return Informer.informer_cnic.ilike(term_pattern)

    # Should be unreachable - search_field is validated against
    # ADMIN_SEARCH_FIELDS by the caller before this is ever invoked.
    raise HTTPException(status_code=400, detail="Unsupported search_field")


# Fields that support the type-ahead suggestion dropdown. Deliberately a
# small subset of ADMIN_SEARCH_FIELDS - suggestions only make sense for
# free-text name fields, not IDs, dates, or enums.
SUGGESTION_FIELDS = {"deceased_name", "deceased_surname"}


def get_grave_search_suggestions(
    search_field: str,
    search_term: str,
    limit: int = 8,
    session: Session = Depends(get_session),
) -> list[str]:
    """
    Type-ahead suggestions for the admin search box. Returns a small list of
    distinct matching values (not full grave records) - the frontend only
    calls this once search_term is 2+ characters, and this endpoint enforces
    that minimum too so it can't be bypassed by calling the API directly.
    """
    term = search_term.strip()
    if search_field not in SUGGESTION_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"search_field must be one of: {', '.join(SUGGESTION_FIELDS)}",
        )
    if len(term) < 2:
        raise HTTPException(status_code=400, detail="search_term must be at least 2 characters")
    if limit < 1 or limit > 10:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 10")

    term_pattern = f"%{term}%"

    if search_field == "deceased_name":
        combined_name = func.concat(
            Grave.deceased_name, " ", func.coalesce(Grave.deceased_surname, "")
        )
        statement = (
            select(combined_name)
            .where(combined_name.ilike(term_pattern))
            .distinct()
            .order_by(combined_name)
            .limit(limit)
        )
    else:  # deceased_surname
        statement = (
            select(Grave.deceased_surname)
            .where(Grave.deceased_surname.is_not(None))
            .where(Grave.deceased_surname.ilike(term_pattern))
            .distinct()
            .order_by(Grave.deceased_surname)
            .limit(limit)
        )

    results = session.exec(statement).all()
    return [value for value in results if value]


def search_graves_with_informers(
    search_field: Optional[str] = None,
    search_term: Optional[str] = None,
    search_term_to: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
) -> GraveWithInformerPaginatedRead:
    """
    Paginated admin grave list (with joined informer columns), matching the
    columns/search fields used on /admin/super-admin/graves/view. No search
    is required - omitting search_field/search_term returns page 1 of
    everything, ordered newest first, same as the old unpaginated behavior.

    search_term_to is only used for date_of_death/date_buried: when set,
    the search becomes an inclusive range (search_term <= column <=
    search_term_to) instead of an exact match.
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size must be between 1 and 100")

    conditions = []
    if search_field is not None or search_term is not None:
        if not search_field or not search_term:
            raise HTTPException(
                status_code=400,
                detail="search_field and search_term must be provided together",
            )
        if search_field not in ADMIN_SEARCH_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid search_field. Must be one of: {', '.join(ADMIN_SEARCH_FIELDS)}",
            )
        if search_term_to and search_field not in ADMIN_DATE_RANGE_FIELDS:
            raise HTTPException(
                status_code=400,
                detail="search_term_to is only supported for date_of_death and date_buried",
            )
        conditions.append(
            _build_admin_search_condition(search_field, search_term, search_term_to)
        )

    count_statement = (
        select(func.count())
        .select_from(Grave)
        .outerjoin(Informer, Grave.id == Informer.grave_id)
    )
    if conditions:
        count_statement = count_statement.where(*conditions)
    total = session.exec(count_statement).one()

    statement = select(Grave, Informer).join(Informer, Grave.id == Informer.grave_id, isouter=True)
    if conditions:
        statement = statement.where(*conditions)
    statement = (
        statement.order_by(Grave.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    results = session.exec(statement).all()

    items = [
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
            date_buried=grave.date_buried,
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
        for grave, informer in results
    ]

    total_pages = (total + page_size - 1) // page_size if total else 0

    return GraveWithInformerPaginatedRead(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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