# app\routes\auth_route.py
from fastapi import APIRouter

from app.controllers.auth_controller import login_user
from app.schemas.user_schema import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

router.post("/login", response_model=TokenResponse)(login_user)