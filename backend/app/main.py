from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers import users

app = FastAPI(
    title="NutriPath API",
    description="Backend API for the NutriPath application",
    version="1.0.0"
)

app.include_router(users.router)

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