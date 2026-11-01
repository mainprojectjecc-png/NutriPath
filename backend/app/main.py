from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers import users, profiles, weight_progress
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="NutriPath API",
    description="Backend API for the NutriPath application",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(weight_progress.router)

@app.get("/")
def home():
    return {
        "message": "Welcome to NutriPath API",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/db-check")
def database_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT DB_NAME()"))
    database_name = result.scalar()

    return {
        "status": "connected",
        "database": database_name
    }