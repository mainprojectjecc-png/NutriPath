from sqlalchemy.orm import Session, aliased

from app.models.coach_suggestion import CoachSuggestion
from app.models.food_change_request import FoodChangeRequest
from app.models.food_item import FoodItem
from app.models.meal import Meal
from app.models.meal_item import MealItem
from app.models.user import User
from app.schemas.food_change_request import (
    CoachSuggestionDetails,
    FoodChangeMealItemDetails,
    FoodChangeRequestResponse,
    PublicUserDetails,
)
from app.schemas.food_item import FoodItemResponse
from app.schemas.meal import MealDetails


def request_details_query(db: Session):
    original_food = aliased(FoodItem)
    requested_food = aliased(FoodItem)
    suggested_food = aliased(FoodItem)
    suggestion = aliased(CoachSuggestion)

    return (
        db.query(
            FoodChangeRequest,
            User.UserID,
            User.FullName,
            User.Email,
            User.Role,
            User.IsActive,
            MealItem,
            Meal,
            original_food,
            requested_food,
            suggestion,
            suggested_food,
        )
        .join(User, User.UserID == FoodChangeRequest.UserID)
        .join(MealItem, MealItem.MealItemID == FoodChangeRequest.MealItemID)
        .join(Meal, Meal.MealID == MealItem.MealID)
        .join(original_food, original_food.FoodID == MealItem.FoodID)
        .outerjoin(
            requested_food,
            requested_food.FoodID == FoodChangeRequest.RequestedFoodID,
        )
        .outerjoin(
            suggestion,
            suggestion.RequestID == FoodChangeRequest.RequestID,
        )
        .outerjoin(
            suggested_food,
            suggested_food.FoodID == suggestion.SuggestedFoodID,
        )
    )


def serialize_request_row(row) -> FoodChangeRequestResponse:
    (
        request,
        user_id,
        user_full_name,
        user_email,
        user_role,
        user_is_active,
        meal_item,
        meal,
        original_food,
        requested_food,
        suggestion,
        suggested_food,
    ) = row

    suggestion_details = None
    if suggestion is not None and suggested_food is not None:
        suggestion_details = CoachSuggestionDetails(
            SuggestionID=suggestion.SuggestionID,
            RequestID=suggestion.RequestID,
            CoachID=suggestion.CoachID,
            SuggestedFoodID=suggestion.SuggestedFoodID,
            Message=suggestion.Message,
            Status=suggestion.Status,
            CreatedAt=suggestion.CreatedAt,
            UpdatedAt=suggestion.UpdatedAt,
            SuggestedFood=FoodItemResponse.model_validate(suggested_food),
        )

    return FoodChangeRequestResponse(
        RequestID=request.RequestID,
        UserID=request.UserID,
        MealItemID=request.MealItemID,
        RequestedFoodID=request.RequestedFoodID,
        Reason=request.Reason,
        Status=request.Status,
        CreatedAt=request.CreatedAt,
        UpdatedAt=request.UpdatedAt,
        User=PublicUserDetails(
            UserID=user_id,
            FullName=user_full_name,
            Email=user_email,
            Role=user_role,
            IsActive=user_is_active,
        ),
        MealItem=FoodChangeMealItemDetails(
            MealItemID=meal_item.MealItemID,
            MealID=meal_item.MealID,
            FoodID=meal_item.FoodID,
            Quantity=meal_item.Quantity,
            ServingUnit=meal_item.ServingUnit,
            Meal=MealDetails.model_validate(meal),
            Food=FoodItemResponse.model_validate(original_food),
        ),
        RequestedFood=(
            FoodItemResponse.model_validate(requested_food)
            if requested_food is not None
            else None
        ),
        Suggestion=suggestion_details,
    )
