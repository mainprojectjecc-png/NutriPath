from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class MealItem(Base):
    __tablename__ = "MealItems"

    MealItemID = Column(Integer, primary_key=True, index=True)
    MealID = Column(Integer, ForeignKey("Meals.MealID"), nullable=False)
    FoodID = Column(Integer, ForeignKey("FoodItems.FoodID"), nullable=False)
    Quantity = Column(Numeric(8, 2), nullable=False)
    ServingUnit = Column(String(50), nullable=False)
    CreatedAt = Column(DateTime, nullable=False, server_default=func.sysutcdatetime())