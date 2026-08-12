# app\routes\hello_route.py
from fastapi import APIRouter

from app.controllers.hello_controller import get_hello, get_bye

router = APIRouter()

router.get("/hello")(get_hello)
router.get("/bye")(get_bye)