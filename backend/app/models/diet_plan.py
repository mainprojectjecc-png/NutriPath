from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class DietPlan(Base):
    __tablename__ = "DietPlans"

    PlanID = Column(Integer, primary_key=True, index=True)

    UserID = Column(
        Integer,
        ForeignKey("Users.UserID"),
        nullable=False
    )

    PlanName = Column(String(100), nullable=False)
    StartDate = Column(Date, nullable=False)
    EndDate = Column(Date, nullable=True)

    Status = Column(
        String(20),
        nullable=False,
        server_default="Active"
    )

    CreatedAt = Column(
        DateTime,
        nullable=False,
        server_default=func.sysutcdatetime()
    )

    UpdatedAt = Column(DateTime, nullable=True)