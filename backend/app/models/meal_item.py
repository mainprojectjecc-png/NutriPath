from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from app.database import Base, utc_now

class MealItem(Base):
    __tablename__ = "MealItems"

    MealItemID = Column(Integer, primary_key=True, index=True)
    MealID = Column(Integer, ForeignKey("Meals.MealID"), nullable=False)
    FoodID = Column(Integer, ForeignKey("FoodItems.FoodID"), nullable=False)
    Quantity = Column(Numeric(8, 2), nullable=False)
    ServingUnit = Column(String(50), nullable=False)
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)