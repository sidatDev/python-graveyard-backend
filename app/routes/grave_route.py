from fastapi import APIRouter

from app.controllers.grave_controller import (
    get_graves,
    get_graves_with_informers,
    get_grave_with_informer,
    create_grave_with_informer,
    update_grave_with_informer,
    delete_grave,
    erase_grave,
    get_deleted_graves_with_informers,
    restore_grave,
    permanent_delete_grave,
)
from app.schemas.grave_schema import (
    GraveRead,
    GraveWithInformerRead,
    GraveInformerDetailRead,
    DeletedGraveWithInformerRead,
)

router = APIRouter(prefix="/graves", tags=["graves"])

router.get("/", response_model=list[GraveRead])(get_graves)
router.get("/deleted", response_model=list[DeletedGraveWithInformerRead])(get_deleted_graves_with_informers)
router.get("/with-informers", response_model=list[GraveWithInformerRead])(get_graves_with_informers)
router.post("/with-informer", response_model=GraveInformerDetailRead, status_code=201)(create_grave_with_informer)
router.get("/{grave_id}/with-informer", response_model=GraveInformerDetailRead)(get_grave_with_informer)
router.patch("/{grave_id}/with-informer", response_model=GraveInformerDetailRead)(update_grave_with_informer)
router.post("/{grave_id}/erase")(erase_grave)
router.post("/{grave_id}/restore")(restore_grave)
router.delete("/{grave_id}/permanent")(permanent_delete_grave)
router.delete("/{grave_id}")(delete_grave)