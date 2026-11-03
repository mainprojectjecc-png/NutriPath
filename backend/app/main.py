import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app import models  # noqa: F401

from app.routers import (
    auth,
    coach,
    diet,
    diet_plans,
    food_change_requests,
    foods,
    meals,
    nutrition,
    profile,
    profiles,
    users,
    weight_progress,
)



app = FastAPI(
    title="NutriPath API",
    description="Backend API for the NutriPath application",
    version="1.0.0",
)
origins = os.getenv(
    "NUTRIPATH_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4179,http://127.0.0.1:4179",
).split(",")
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
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(diet_plans.router)
app.include_router(weight_progress.router)
app.include_router(foods.router)
app.include_router(meals.router)
app.include_router(food_change_requests.router)
app.include_router(coach.router)
app.include_router(diet.router)


@app.get("/")
def home():
    return {"message": "Welcome to NutriPath API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def database_check(db: Session = Depends(get_db)):
    if db.get_bind().dialect.name == "mssql":
        result = db.execute(text("SELECT DB_NAME()"))
        database_name = result.scalar()
    else:
        result = db.execute(text("SELECT name FROM pragma_database_list WHERE name = 'main'"))
        database_name = result.scalar()

    return {"status": "connected", "database": database_name}
