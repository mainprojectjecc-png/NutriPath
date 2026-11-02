import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import models  # noqa: F401
from app.routers import auth, nutrition, profile

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NutriPath API", version="1.0.0")
origins = os.getenv("NUTRIPATH_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(nutrition.router)


@app.get("/health")
def health():
    return {"status": "ok"}
