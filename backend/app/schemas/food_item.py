from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FoodItemResponse(BaseModel):
    FoodID: int
    FoodName: str
    Category: str | None
    Calories: Decimal
    Protein: Decimal
    Carbs: Decimal
    Fat: Decimal
    Fiber: Decimal
    ServingSize: str | None

    model_config = ConfigDict(from_attributes=True)
