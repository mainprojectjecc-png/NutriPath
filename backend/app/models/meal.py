from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Meal(Base):
    __tablename__ = "Meals"

    MealID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    PlanID = Column(Integer, ForeignKey("DietPlans.PlanID"))
    MealDate = Column(Date, nullable=False)
    MealType = Column(String(30), nullable=False)
    Notes = Column(String(500))
    CreatedAt = Column(DateTime, nullable=False, server_default=func.sysutcdatetime())