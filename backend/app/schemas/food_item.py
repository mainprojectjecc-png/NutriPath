from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FoodItemResponse(BaseModel):
    FoodID: int
    CatalogID: str | None
    FoodName: str
    Category: str | None
    Calories: Decimal
    Protein: Decimal
    Carbs: Decimal
    Fat: Decimal
    Fiber: Decimal
    ServingSize: str | None
    Ingredients: str | None = None
    Allergens: str | None = None
    DietaryClassifications: str | None = None
    AnimalDerivedIngredients: str | None = None
    CrossContactWarnings: str | None = None
    IsVerified: bool = False
    IsVegetarian: bool | None = None
    IsVegan: bool | None = None
    ContainsEgg: bool | None = None
    ContainsDairy: bool | None = None
    ContainsHoney: bool | None = None
    ContainsFish: bool | None = None
    ContainsSeafood: bool | None = None
    ContainsMeat: bool | None = None
    SafetyStatus: str = "unknown"

    model_config = ConfigDict(from_attributes=True)
