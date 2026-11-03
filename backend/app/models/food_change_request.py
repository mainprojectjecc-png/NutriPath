from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base, utc_now


class FoodChangeRequest(Base):
    __tablename__ = "FoodChangeRequests"

    RequestID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)

    # Existing meal-based requests
    MealItemID = Column(
        Integer,
        ForeignKey("MealItems.MealItemID"),
        nullable=True,
    )

    # New nutrition-tracker requests
    NutritionLogID = Column(
        Integer,
        ForeignKey("nutrition_logs.id"),
        nullable=True,
    )

    RequestedFoodID = Column(
        Integer,
        ForeignKey("FoodItems.FoodID"),
        nullable=True,
    )

    Reason = Column(String(500))
    Status = Column(String(20), nullable=False, server_default="Pending")
    CreatedAt = Column(DateTime, nullable=False, default=utc_now)
    UpdatedAt = Column(DateTime)