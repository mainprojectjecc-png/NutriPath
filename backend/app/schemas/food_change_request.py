from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.food_item import FoodItemResponse
from app.schemas.meal import MealDetails

FoodChangeStatus = Literal["Pending", "Reviewed", "Accepted", "Rejected"]
SuggestionStatus = Literal["Pending", "Accepted", "Rejected"]


class FoodChangeRequestCreate(BaseModel):
    MealItemID: int = Field(gt=0)
    RequestedFoodID: int | None = Field(default=None, gt=0)
    Reason: str = Field(min_length=1, max_length=500)


class CoachSuggestionDetails(BaseModel):
    SuggestionID: int
    RequestID: int
    CoachID: int
    SuggestedFoodID: int
    Message: str | None
    Status: SuggestionStatus
    CreatedAt: datetime
    UpdatedAt: datetime | None
    SuggestedFood: FoodItemResponse


class PublicUserDetails(BaseModel):
    UserID: int
    FullName: str
    Email: str
    Role: str
    IsActive: bool

    model_config = ConfigDict(from_attributes=True)


class FoodChangeMealItemDetails(BaseModel):
    MealItemID: int
    MealID: int
    FoodID: int
    Quantity: Decimal
    ServingUnit: str
    Meal: MealDetails
    Food: FoodItemResponse


class FoodChangeRequestResponse(BaseModel):
    RequestID: int
    UserID: int
    MealItemID: int
    RequestedFoodID: int | None
    Reason: str | None
    Status: FoodChangeStatus
    CreatedAt: datetime
    UpdatedAt: datetime | None
    User: PublicUserDetails | None = None
    MealItem: FoodChangeMealItemDetails
    RequestedFood: FoodItemResponse | None
    Suggestion: CoachSuggestionDetails | None
