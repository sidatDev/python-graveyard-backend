from fastapi import HTTPException, Depends
from sqlmodel import Session, select

from app.db.connection import get_session
from app.models.user_model import User
from app.schemas.user_schema import LoginRequest, TokenResponse
from app.utils.jwt_handler import create_access_token


def login_user(credentials: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = session.exec(select(User).where(User.email == credentials.email)).first()

    if not user or user.password != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token({"sub": str(user.id)})

    return TokenResponse(access_token=token, user=user)