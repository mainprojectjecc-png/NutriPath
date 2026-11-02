from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.food_item import FoodItemResponse

MealType = Literal["Breakfast", "Lunch", "Dinner", "Snack"]


class MealCreate(BaseModel):
    MealDate: date
    MealType: MealType
    PlanID: int | None = Field(default=None, gt=0)
    Notes: str | None = Field(default=None, max_length=500)


class MealItemCreate(BaseModel):
    FoodID: int = Field(gt=0)
    Quantity: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    ServingUnit: str = Field(min_length=1, max_length=50)


class MealItemUpdate(BaseModel):
    Quantity: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=8,
        decimal_places=2,
    )
    ServingUnit: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    @model_validator(mode="after")
    def require_update_field(self) -> "MealItemUpdate":
        if self.Quantity is None and self.ServingUnit is None:
            raise ValueError("At least one field must be provided.")
        return self


class MealDetails(BaseModel):
    MealID: int
    MealDate: date
    MealType: str
    Notes: str | None
    PlanID: int | None

    model_config = ConfigDict(from_attributes=True)


class MealItemResponse(BaseModel):
    MealItemID: int
    FoodID: int
    Quantity: Decimal
    ServingUnit: str
    Food: FoodItemResponse


class MealResponse(BaseModel):
    MealID: int
    UserID: int
    PlanID: int | None
    MealDate: date
    MealType: str
    Notes: str | None
    Items: list[MealItemResponse]

    model_config = ConfigDict(from_attributes=True)
