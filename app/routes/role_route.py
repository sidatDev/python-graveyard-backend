# app\routes\role_route.py
from fastapi import APIRouter

from app.controllers.role_controller import (
    create_role,
    get_roles,
    get_role,
    update_role,
    erase_role,
    get_deleted_roles,
    restore_role,
    permanent_delete_role,
)
from app.schemas.role_schema import RoleRead, RoleReadWithCount, DeletedRoleRead

router = APIRouter(prefix="/roles", tags=["roles"])

router.post("/", response_model=RoleRead, status_code=201)(create_role)
router.get("/", response_model=list[RoleReadWithCount])(get_roles)
router.get("/deleted", response_model=list[DeletedRoleRead])(get_deleted_roles)
router.get("/{role_id}", response_model=RoleRead)(get_role)
router.patch("/{role_id}", response_model=RoleRead)(update_role)
router.post("/{role_id}/erase", status_code=204)(erase_role)
router.post("/{role_id}/restore", response_model=RoleRead)(restore_role)
router.delete("/{role_id}/permanent", status_code=204)(permanent_delete_role)