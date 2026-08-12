# app\controllers\role_controller.py
import uuid
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlmodel import Session, select, func

from app.db.connection import get_session
from app.models.role_model import Role, DeletedRole
from app.models.user_model import User
from app.models.deleted_user_model import DeletedUser
from app.schemas.role_schema import RoleCreate, RoleUpdate, RoleReadWithCount


def create_role(role_in: RoleCreate, session: Session = Depends(get_session)) -> Role:
    existing = session.exec(select(Role).where(Role.name == role_in.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="A role with this name already exists")

    role = Role(name=role_in.name, permissions=role_in.permissions)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


def get_roles(session: Session = Depends(get_session)) -> list[RoleReadWithCount]:
    statement = (
        select(Role, func.count(User.id))
        .join(User, User.role_id == Role.id, isouter=True)
        .group_by(Role.id)
        .order_by(Role.created_at.desc())
    )
    results = session.exec(statement).all()

    return [
        RoleReadWithCount(**role.model_dump(), user_count=int(count))
        for role, count in results
    ]


def get_role(role_id: uuid.UUID, session: Session = Depends(get_session)) -> Role:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


def update_role(
    role_id: uuid.UUID, role_in: RoleUpdate, session: Session = Depends(get_session)
) -> Role:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role_in.name is not None and role_in.name != role.name:
        existing = session.exec(select(Role).where(Role.name == role_in.name)).first()
        if existing:
            raise HTTPException(status_code=400, detail="A role with this name already exists")
        role.name = role_in.name

    if role_in.permissions is not None:
        role.permissions = role_in.permissions

    session.add(role)
    session.commit()
    session.refresh(role)
    return role


def erase_role(role_id: uuid.UUID, session: Session = Depends(get_session)) -> None:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Deactivate currently-active users assigned this role, and remember
    # exactly who — so Restore can reactivate only these users.
    # role_id itself is deliberately left untouched: no FK to break anymore.
    assigned_users = session.exec(
        select(User).where(User.role_id == role_id, User.is_active == True)  # noqa: E712
    ).all()

    deactivated_ids = [str(user.id) for user in assigned_users]
    for user in assigned_users:
        user.is_active = False
        session.add(user)

    deleted_role = DeletedRole(
        id=role.id,
        name=role.name,
        permissions=role.permissions,
        created_at=role.created_at,
        updated_at=role.updated_at,
        deleted_at=datetime.utcnow(),
        deactivated_user_ids=deactivated_ids,
    )
    session.add(deleted_role)
    session.delete(role)
    session.commit()


def get_deleted_roles(session: Session = Depends(get_session)) -> list[DeletedRole]:
    return session.exec(select(DeletedRole).order_by(DeletedRole.deleted_at.desc())).all()


def restore_role(role_id: uuid.UUID, session: Session = Depends(get_session)) -> Role:
    deleted_role = session.get(DeletedRole, role_id)
    if not deleted_role:
        raise HTTPException(status_code=404, detail="Deleted role not found")

    existing = session.exec(select(Role).where(Role.name == deleted_role.name)).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A role with this name already exists. Rename it before restoring.",
        )

    role = Role(
        id=deleted_role.id,
        name=deleted_role.name,
        permissions=deleted_role.permissions,
        created_at=deleted_role.created_at,
        updated_at=deleted_role.updated_at,
    )
    session.add(role)

    # Reactivate exactly the users this role's Erase deactivated. Their
    # role_id was never touched, so they're already correctly linked.
    if deleted_role.deactivated_user_ids:
        ids = [uuid.UUID(uid) for uid in deleted_role.deactivated_user_ids]
        users_to_reactivate = session.exec(select(User).where(User.id.in_(ids))).all()
        for user in users_to_reactivate:
            user.is_active = True
            session.add(user)

    session.delete(deleted_role)
    session.commit()
    session.refresh(role)
    return role


def permanent_delete_role(role_id: uuid.UUID, session: Session = Depends(get_session)) -> None:
    deleted_role = session.get(DeletedRole, role_id)
    if not deleted_role:
        raise HTTPException(status_code=404, detail="Deleted role not found")

    # This is the only point where the link actually breaks.
    assigned_users = session.exec(select(User).where(User.role_id == role_id)).all()
    for user in assigned_users:
        user.role_id = None
        session.add(user)

    assigned_deleted_users = session.exec(
        select(DeletedUser).where(DeletedUser.role_id == role_id)
    ).all()
    for du in assigned_deleted_users:
        du.role_id = None
        session.add(du)

    session.delete(deleted_role)
    session.commit()