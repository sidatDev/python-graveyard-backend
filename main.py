# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.hello_route import router as hello_router
from app.routes.db_route import router as db_router
from app.routes.user_route import router as user_router
from app.routes.auth_route import router as auth_router
from app.routes.grave_route import router as grave_router
from app.routes.role_route import router as role_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.0.144:3000",
        "https://python-graveyard-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello_router)
app.include_router(db_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(grave_router)
app.include_router(role_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)