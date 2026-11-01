from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class FoodItem(Base):
    __tablename__ = "FoodItems"

    FoodID = Column(Integer, primary_key=True, index=True)
    FoodName = Column(String(150), nullable=False)
    Category = Column(String(50))
    Calories = Column(Numeric(8, 2), nullable=False)
    Protein = Column(Numeric(8, 2), nullable=False, server_default="0")
    Carbs = Column(Numeric(8, 2), nullable=False, server_default="0")
    Fat = Column(Numeric(8, 2), nullable=False, server_default="0")
    Fiber = Column(Numeric(8, 2), nullable=False, server_default="0")
    ServingSize = Column(String(50))
    IsActive = Column(Boolean, nullable=False, server_default="1")
    CreatedAt = Column(DateTime, nullable=False, server_default=func.sysutcdatetime())