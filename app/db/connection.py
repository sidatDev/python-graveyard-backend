# app\db\connection.py
import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)  # echo=True logs SQL, turn off in prod

def get_session():
    with Session(engine) as session:
        yield session