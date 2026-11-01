from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "Users"

    UserID = Column(Integer, primary_key=True, index=True)
    FullName = Column(String(100), nullable=False)
    Email = Column(String(150), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(255), nullable=False)
    Role = Column(String(20), nullable=False, server_default="User")
    IsActive = Column(Boolean, nullable=False, server_default="1")
    CreatedAt = Column(DateTime, nullable=False, server_default=func.sysutcdatetime())
    UpdatedAt = Column(DateTime, nullable=True)