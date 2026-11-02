from pydantic import BaseModel, Field

from app.schemas.food_change_request import FoodChangeRequestResponse


class CoachSuggestionCreate(BaseModel):
    SuggestedFoodID: int = Field(gt=0)
    Message: str | None = Field(default=None, max_length=1000)


class CoachRequestResponse(FoodChangeRequestResponse):
    pass
