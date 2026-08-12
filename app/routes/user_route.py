# app/routes/user_route.py
# from fastapi import APIRouter
# import uuid

# from app.controllers.user_controller import (
#     create_user,
#     get_users,
#     get_user,
#     update_user,
#     delete_user,
# )
# from app.schemas.user_schema import UserCreate, UserUpdate, UserRead

# router = APIRouter(prefix="/users", tags=["users"])

# router.post("/", response_model=UserRead, status_code=201)(create_user)
# router.get("/", response_model=list[UserRead])(get_users)
# router.get("/{user_id}", response_model=UserRead)(get_user)
# router.patch("/{user_id}", response_model=UserRead)(update_user)
# router.delete("/{user_id}")(delete_user)




from fastapi import APIRouter

from app.controllers.user_controller import (
    create_user,
    get_users,
    get_user,
    update_user,
    delete_user,
    erase_user,
    get_deleted_users,
    restore_user,
    permanent_delete_user,
)
from app.schemas.user_schema import UserCreate, UserUpdate, UserRead, DeletedUserRead

router = APIRouter(prefix="/users", tags=["users"])

router.post("/", response_model=UserRead, status_code=201)(create_user)
router.get("/", response_model=list[UserRead])(get_users)
router.get("/deleted", response_model=list[DeletedUserRead])(get_deleted_users)
router.get("/{user_id}", response_model=UserRead)(get_user)
router.patch("/{user_id}", response_model=UserRead)(update_user)
router.post("/{user_id}/erase")(erase_user)
router.post("/{user_id}/restore")(restore_user)
router.delete("/{user_id}/permanent")(permanent_delete_user)
router.delete("/{user_id}")(delete_user)