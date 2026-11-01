from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class UserProfile(Base):
    __tablename__ = "UserProfiles"

    ProfileID = Column(Integer, primary_key=True, index=True)

    UserID = Column(
        Integer,
        ForeignKey("Users.UserID"),
        unique=True,
        nullable=False
    )

    Age = Column(Integer, nullable=True)
    Gender = Column(String(20), nullable=True)
    HeightCm = Column(Numeric(5, 2), nullable=True)
    CurrentWeightKg = Column(Numeric(6, 2), nullable=True)
    TargetWeightKg = Column(Numeric(6, 2), nullable=True)
    HealthGoal = Column(String(255), nullable=True)

    CreatedAt = Column(
        DateTime,
        nullable=False,
        server_default=func.sysutcdatetime()
    )

    UpdatedAt = Column(DateTime, nullable=True)