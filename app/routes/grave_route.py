from fastapi import APIRouter

from app.controllers.grave_controller import (
    get_graves,
    search_graves,
    get_public_grave_search_suggestions,
    get_graves_with_informers,
    search_graves_with_informers,
    get_grave_search_suggestions,
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
    GravePaginatedRead,
    GraveWithInformerRead,
    GraveWithInformerPaginatedRead,
    GraveInformerDetailRead,
    DeletedGraveWithInformerRead,
)

router = APIRouter(prefix="/graves", tags=["graves"])

router.get("/", response_model=list[GraveRead])(get_graves)
router.get("/search", response_model=GravePaginatedRead)(search_graves)
router.get("/suggestions", response_model=list[str])(get_public_grave_search_suggestions)
router.get("/deleted", response_model=list[DeletedGraveWithInformerRead])(get_deleted_graves_with_informers)
router.get("/with-informers", response_model=list[GraveWithInformerRead])(get_graves_with_informers)
router.get("/with-informers/search", response_model=GraveWithInformerPaginatedRead)(search_graves_with_informers)
router.get("/with-informers/suggestions", response_model=list[str])(get_grave_search_suggestions)
router.post("/with-informer", response_model=GraveInformerDetailRead, status_code=201)(create_grave_with_informer)
router.get("/{grave_id}/with-informer", response_model=GraveInformerDetailRead)(get_grave_with_informer)
router.patch("/{grave_id}/with-informer", response_model=GraveInformerDetailRead)(update_grave_with_informer)
router.post("/{grave_id}/erase")(erase_grave)
router.post("/{grave_id}/restore")(restore_grave)
router.delete("/{grave_id}/permanent")(permanent_delete_grave)
router.delete("/{grave_id}")(delete_grave)