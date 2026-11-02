from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.food_item import FoodItemResponse
from app.schemas.meal import MealDetails


FoodChangeStatus = Literal["Pending", "Reviewed", "Accepted", "Rejected"]
SuggestionStatus = Literal["Pending", "Accepted", "Rejected"]


class FoodChangeRequestCreate(BaseModel):
    MealItemID: int | None = Field(default=None, gt=0)
    NutritionLogID: int | None = Field(default=None, gt=0)
    RequestedFoodID: int | None = Field(default=None, gt=0)
    Reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_food_reference(self):
        if (self.MealItemID is None) == (self.NutritionLogID is None):
            raise ValueError(
                "Provide exactly one of MealItemID or NutritionLogID."
            )
        return self


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

    model_config = ConfigDict(from_attributes=True)


class FoodChangeMealItemDetails(BaseModel):
    MealItemID: int
    MealID: int
    FoodID: int
    Quantity: Decimal
    ServingUnit: str
    Meal: MealDetails
    Food: FoodItemResponse


class FoodChangeNutritionLogDetails(BaseModel):
    id: int
    food_id: str
    food_name: str
    emoji: str
    meal_type: str
    quantity: float
    serving_label: str
    serving_grams: float
    calories: float
    protein: float
    carbs: float
    fats: float
    date: date
    model_config = ConfigDict(from_attributes=True)


class FoodChangeRequestResponse(BaseModel):
    RequestID: int
    UserID: int
    MealItemID: int | None
    NutritionLogID: int | None
    RequestedFoodID: int | None
    Reason: str | None
    Status: FoodChangeStatus
    CreatedAt: datetime
    UpdatedAt: datetime | None

    User: PublicUserDetails | None = None
    MealItem: FoodChangeMealItemDetails | None = None
    NutritionLog: FoodChangeNutritionLogDetails | None = None
    RequestedFood: FoodItemResponse | None = None
    Suggestion: CoachSuggestionDetails | None = None