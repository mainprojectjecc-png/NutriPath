
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# NutriPath MSSQL Database Connection
DATABASE_URL = (
    "mssql+pyodbc://@localhost/NutriPathDB"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Trusted_Connection=yes"
    "&TrustServerCertificate=yes"
)

# Create SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

# Database Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()


# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
