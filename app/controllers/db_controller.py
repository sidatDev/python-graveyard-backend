from sqlmodel import Session, select
from app.db.connection import engine
from app.models.user_model import User

def check_db_connection() -> dict:
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return {"connected": True, "user_count": len(users)}