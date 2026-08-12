from fastapi import APIRouter

from app.controllers.db_controller import check_db_connection

router = APIRouter()

router.get("/health/db")(check_db_connection)