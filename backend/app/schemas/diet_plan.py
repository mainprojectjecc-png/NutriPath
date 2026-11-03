from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.meal import MealType


class GenerateDietPlanInput(BaseModel):
    StartDate: date = Field(default_factory=date.today)
    Days: int = Field(default=7, ge=1, le=7)


class DietPlanItemInput(BaseModel):
    FoodID: int = Field(gt=0)
    Quantity: Decimal = Field(gt=0, le=50, max_digits=8, decimal_places=2)
    ServingUnit: str = Field(default="serving", min_length=1, max_length=50)


class DietPlanMealInput(BaseModel):
    MealDate: date
    MealType: MealType
    Notes: str | None = Field(default=None, max_length=500)
    Items: list[DietPlanItemInput] = Field(min_length=1, max_length=12)


class DietPlanCreate(BaseModel):
    PlanName: str = Field(min_length=1, max_length=100)
    StartDate: date
    EndDate: date
    Meals: list[DietPlanMealInput] = Field(min_length=4, max_length=28)

    @field_validator("PlanName")
    @classmethod
    def trim_plan_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlanName must contain at least one non-whitespace character.")
        return value

    @model_validator(mode="after")
    def validate_meal_dates(self):
        if self.EndDate < self.StartDate:
            raise ValueError("EndDate must be on or after StartDate.")
        if (self.EndDate - self.StartDate).days >= 7:
            raise ValueError("A meal plan can cover at most seven days.")
        expected_dates = {
            date.fromordinal(self.StartDate.toordinal() + offset)
            for offset in range((self.EndDate - self.StartDate).days + 1)
        }
        meals_by_date: dict[date, set[str]] = {}
        for meal in self.Meals:
            if meal.MealDate not in expected_dates:
                raise ValueError("Every meal date must be within the plan date range.")
            types = meals_by_date.setdefault(meal.MealDate, set())
            if meal.MealType in types:
                raise ValueError("Each day can contain only one meal of each type.")
            types.add(meal.MealType)
        if set(meals_by_date) != expected_dates or any(
            types != {"Breakfast", "Lunch", "Dinner", "Snack"}
            for types in meals_by_date.values()
        ):
            raise ValueError("Each plan day must include breakfast, lunch, dinner, and a snack.")
        return self


class DietPlanUpdate(BaseModel):
    PlanName: str | None = Field(default=None, min_length=1, max_length=100)
    Status: Literal["Active", "Paused", "Completed"] | None = None

    @field_validator("PlanName")
    @classmethod
    def trim_plan_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("PlanName must contain at least one non-whitespace character.")
        return value

    @model_validator(mode="after")
    def require_update_field(self):
        if self.PlanName is None and self.Status is None:
            raise ValueError("At least one field must be provided.")
        return self
