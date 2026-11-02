from sqlalchemy.orm import Session, aliased

from app.models.coach_suggestion import CoachSuggestion
from app.models.food_change_request import FoodChangeRequest
from app.models.food_item import FoodItem
from app.models.meal import Meal
from app.models.meal_item import MealItem
from app.models.models import NutritionLog
from app.models.user import User

from app.schemas.food_change_request import (
    CoachSuggestionDetails,
    FoodChangeMealItemDetails,
    FoodChangeNutritionLogDetails,
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
            MealItem,
            Meal,
            original_food,
            NutritionLog,
            requested_food,
            suggestion,
            suggested_food,
        )
        .join(User, User.UserID == FoodChangeRequest.UserID)
        .outerjoin(
            MealItem,
            MealItem.MealItemID == FoodChangeRequest.MealItemID,
        )
        .outerjoin(
            Meal,
            Meal.MealID == MealItem.MealID,
        )
        .outerjoin(
            original_food,
            original_food.FoodID == MealItem.FoodID,
        )
        .outerjoin(
            NutritionLog,
            NutritionLog.id == FoodChangeRequest.NutritionLogID,
        )
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
        meal_item,
        meal,
        original_food,
        nutrition_log,
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

    meal_details = None

    if meal_item is not None and meal is not None and original_food is not None:
        meal_details = FoodChangeMealItemDetails(
            MealItemID=meal_item.MealItemID,
            MealID=meal_item.MealID,
            FoodID=meal_item.FoodID,
            Quantity=meal_item.Quantity,
            ServingUnit=meal_item.ServingUnit,
            Meal=MealDetails.model_validate(meal),
            Food=FoodItemResponse.model_validate(original_food),
        )

    nutrition_details = None

    if nutrition_log is not None:
        nutrition_details = FoodChangeNutritionLogDetails(
            id=nutrition_log.id,
            food_id=nutrition_log.food_id,
            food_name=nutrition_log.food_name,
            emoji=nutrition_log.emoji,
            meal_type=nutrition_log.meal_type,
            quantity=nutrition_log.quantity,
            serving_label=nutrition_log.serving_label,
            serving_grams=nutrition_log.serving_grams,
            calories=nutrition_log.calories,
            protein=nutrition_log.protein,
            carbs=nutrition_log.carbs,
            fats=nutrition_log.fats,
            date=nutrition_log.logged_on,
        )

    return FoodChangeRequestResponse(
        RequestID=request.RequestID,
        UserID=request.UserID,
        MealItemID=request.MealItemID,
        NutritionLogID=request.NutritionLogID,
        RequestedFoodID=request.RequestedFoodID,
        Reason=request.Reason,
        Status=request.Status,
        CreatedAt=request.CreatedAt,
        UpdatedAt=request.UpdatedAt,
        User=PublicUserDetails(
            UserID=user_id,
            FullName=user_full_name,
        ),
        MealItem=meal_details,
        NutritionLog=nutrition_details,
        RequestedFood=(
            FoodItemResponse.model_validate(requested_food)
            if requested_food is not None
            else None
        ),
        Suggestion=suggestion_details,
    )