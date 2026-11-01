from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class CoachSuggestion(Base):
    __tablename__ = "CoachSuggestions"

    SuggestionID = Column(Integer, primary_key=True, index=True)
    RequestID = Column(Integer, ForeignKey("FoodChangeRequests.RequestID"), nullable=False, unique=True)
    CoachID = Column(Integer, ForeignKey("Users.UserID"), nullable=False)
    SuggestedFoodID = Column(Integer, ForeignKey("FoodItems.FoodID"), nullable=False)
    Message = Column(String(1000))
    Status = Column(String(20), nullable=False, server_default="Pending")
    CreatedAt = Column(DateTime, nullable=False, server_default=func.sysutcdatetime())
    UpdatedAt = Column(DateTime)