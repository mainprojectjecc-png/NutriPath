from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import true
from sqlalchemy.orm import Session

from app.security import current_user as get_current_user
from app.models import User
from app.database import get_db
from app.models.coach_suggestion import CoachSuggestion
from app.models.food_change_request import FoodChangeRequest
from app.models.food_item import FoodItem
from app.models.meal import Meal
from app.models.meal_item import MealItem
from app.schemas.food_change_request import (
    FoodChangeRequestCreate,
    FoodChangeRequestResponse,
)
from app.services.food_change_requests import (
    request_details_query,
    serialize_request_row,
)
from app.services.transactions import commit_or_raise
from app.services.food_emojis import (
    DEFAULT_FOOD_EMOJI,
    get_canonical_food_emoji,
    get_canonical_food_serving,
)

from app.models.models import NutritionLog

router = APIRouter(
    prefix="/api/v1/food-change-requests",
    tags=["Food Change Requests"],
)


@router.get(
    "/",
    response_model=list[FoodChangeRequestResponse],
    summary="List the current user's food change requests",
)
def get_food_change_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FoodChangeRequestResponse]:
    rows = (
        request_details_query(db)
        .filter(FoodChangeRequest.UserID == current_user.id)
        .order_by(
            FoodChangeRequest.CreatedAt.desc(),
            FoodChangeRequest.RequestID.desc(),
        )
        .all()
    )
    return [serialize_request_row(row) for row in rows]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_owned_request(db: Session, request_id: int, user_id: int):
    request = (
        db.query(FoodChangeRequest)
        .filter(
            FoodChangeRequest.RequestID == request_id,
            FoodChangeRequest.UserID == user_id,
        )
        .first()
    )
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food change request not found",
        )
    if request.Status != "Reviewed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This food change request has no pending suggestion.",
        )

    suggestion = (
        db.query(CoachSuggestion)
        .filter(CoachSuggestion.RequestID == request_id)
        .first()
    )
    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found",
        )
    if suggestion.Status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This suggestion has already been resolved.",
        )
    return request, suggestion


def _get_request_response(db: Session, request_id: int) -> FoodChangeRequestResponse:
    row = (
        request_details_query(db)
        .filter(FoodChangeRequest.RequestID == request_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food change request not found",
        )
    return serialize_request_row(row)


@router.post(
    "/",
    response_model=FoodChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a food replacement",
)
def create_food_change_request(
    request_data: FoodChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FoodChangeRequestResponse:
    user_id = current_user.id

    if request_data.MealItemID is not None:
        meal_item = (
            db.query(MealItem)
            .join(Meal, Meal.MealID == MealItem.MealID)
            .filter(
                MealItem.MealItemID == request_data.MealItemID,
                Meal.UserID == user_id,
            )
            .first()
        )

        if meal_item is None:
            raise HTTPException(
                status_code=404,
                detail="Meal item not found",
            )

    else:
        nutrition_log = (
            db.query(NutritionLog)
            .filter(
                NutritionLog.id == request_data.NutritionLogID,
                NutritionLog.user_id == user_id,
            )
            .first()
        )

        if nutrition_log is None:
            raise HTTPException(
                status_code=404,
                detail="Nutrition log entry not found",
            )

    if request_data.RequestedFoodID is not None:
        food = (
            db.query(FoodItem)
            .filter(
                FoodItem.FoodID == request_data.RequestedFoodID,
                FoodItem.IsActive == true(),
            )
            .first()
        )

        if food is None:
            raise HTTPException(
                status_code=404,
                detail="Active replacement food not found",
            )

    request_query = db.query(FoodChangeRequest.RequestID).filter(
        FoodChangeRequest.UserID == user_id,
        FoodChangeRequest.Status.in_(("Pending", "Reviewed")),
    )
    if request_data.MealItemID is not None:
        request_query = request_query.filter(
            FoodChangeRequest.MealItemID == request_data.MealItemID
        )
    else:
        request_query = request_query.filter(
            FoodChangeRequest.NutritionLogID == request_data.NutritionLogID
        )
    if request_query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active replacement request already exists for this food.",
        )

    request = FoodChangeRequest(
        UserID=user_id,
        MealItemID=request_data.MealItemID,
        NutritionLogID=request_data.NutritionLogID,
        RequestedFoodID=request_data.RequestedFoodID,
        Reason=request_data.Reason,
        Status="Pending",
    )

    db.add(request)
    commit_or_raise(db)
    db.refresh(request)

    row = (
        request_details_query(db)
        .filter(FoodChangeRequest.RequestID == request.RequestID)
        .first()
    )

    return serialize_request_row(row)

@router.post(
    "/{request_id}/accept",
    response_model=FoodChangeRequestResponse,
    summary="Accept a coach food suggestion",
)
def accept_food_suggestion(
    request_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FoodChangeRequestResponse:
    user_id = current_user.id

    request, suggestion = _get_owned_request(db, request_id, user_id)

    suggested_food = (
        db.query(FoodItem)
        .filter(
            FoodItem.FoodID == suggestion.SuggestedFoodID,
            FoodItem.IsActive == true(),
        )
        .first()
    )

    if suggested_food is None:
        raise HTTPException(
            status_code=409,
            detail="The suggested food is no longer active.",
        )

    now = _utcnow()

    # Update the original MealItem if this is a meal-based request.
    if request.MealItemID is not None:
        meal_item = (
            db.query(MealItem)
            .join(Meal, Meal.MealID == MealItem.MealID)
            .filter(
                MealItem.MealItemID == request.MealItemID,
                Meal.UserID == user_id,
            )
            .first()
        )

        if meal_item is None:
            raise HTTPException(
                status_code=404,
                detail="Meal item not found",
            )

        item_updated = (
            db.query(MealItem)
            .filter(MealItem.MealItemID == meal_item.MealItemID)
            .update(
                {MealItem.FoodID: suggestion.SuggestedFoodID},
                synchronize_session=False,
            )
        )

    # Update the NutritionLog if this is a nutrition-tracker request.
    else:
        nutrition_log = (
            db.query(NutritionLog)
            .filter(
                NutritionLog.id == request.NutritionLogID,
                NutritionLog.user_id == user_id,
            )
            .first()
        )

        if nutrition_log is None:
            raise HTTPException(
                status_code=404,
                detail="Nutrition log entry not found",
            )
        if suggested_food.CatalogID is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The suggested food cannot replace this nutrition entry because it has no catalog identifier.",
            )

        serving = get_canonical_food_serving(suggested_food.CatalogID)
        serving_label, serving_grams = serving or (
            suggested_food.ServingSize or nutrition_log.serving_label,
            nutrition_log.serving_grams,
        )
        quantity = nutrition_log.quantity
        item_updated = (
            db.query(NutritionLog)
            .filter(
                NutritionLog.id == nutrition_log.id,
                NutritionLog.user_id == user_id,
            )
            .update(
                {
                    NutritionLog.food_id: suggested_food.CatalogID,
                    NutritionLog.food_name: suggested_food.FoodName,
                    NutritionLog.emoji: (
                        get_canonical_food_emoji(suggested_food.CatalogID)
                        or DEFAULT_FOOD_EMOJI
                    ),
                    NutritionLog.serving_label: serving_label,
                    NutritionLog.serving_grams: serving_grams,
                    NutritionLog.calories: float(suggested_food.Calories) * quantity,
                    NutritionLog.protein: float(suggested_food.Protein) * quantity,
                    NutritionLog.carbs: float(suggested_food.Carbs) * quantity,
                    NutritionLog.fats: float(suggested_food.Fat) * quantity,
                },
                synchronize_session=False,
            )
        )

    suggestion_updated = (
        db.query(CoachSuggestion)
        .filter(
            CoachSuggestion.SuggestionID == suggestion.SuggestionID,
            CoachSuggestion.Status == "Pending",
        )
        .update(
            {
                CoachSuggestion.Status: "Accepted",
                CoachSuggestion.UpdatedAt: now,
            },
            synchronize_session=False,
        )
    )

    request_updated = (
        db.query(FoodChangeRequest)
        .filter(
            FoodChangeRequest.RequestID == request_id,
            FoodChangeRequest.UserID == user_id,
            FoodChangeRequest.Status == "Reviewed",
        )
        .update(
            {
                FoodChangeRequest.Status: "Accepted",
                FoodChangeRequest.UpdatedAt: now,
            },
            synchronize_session=False,
        )
    )

    if (
        suggestion_updated != 1
        or request_updated != 1
        or item_updated != 1
    ):
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="The request or suggestion has changed; reload and try again.",
        )

    commit_or_raise(db)
    db.expire_all()

    return _get_request_response(db, request_id)

@router.get(
    "/{request_id}",
    response_model=FoodChangeRequestResponse,
    summary="Get one of your food change requests",
)
def get_food_change_request(
    request_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FoodChangeRequestResponse:
    row = (
        request_details_query(db)
        .filter(
            FoodChangeRequest.RequestID == request_id,
            FoodChangeRequest.UserID == current_user.id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food change request not found",
        )
    return serialize_request_row(row)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a pending food change request",
)
def delete_food_change_request(
    request_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    request = (
        db.query(FoodChangeRequest)
        .filter(
            FoodChangeRequest.RequestID == request_id,
            FoodChangeRequest.UserID == current_user.id,
        )
        .first()
    )
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food change request not found",
        )
    if request.Status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending food change requests can be canceled.",
        )
    if (
        db.query(CoachSuggestion.SuggestionID)
        .filter(CoachSuggestion.RequestID == request_id)
        .first()
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Food change request has a suggestion and cannot be canceled.",
        )

    deleted = (
        db.query(FoodChangeRequest)
        .filter(
            FoodChangeRequest.RequestID == request_id,
            FoodChangeRequest.UserID == current_user.id,
            FoodChangeRequest.Status == "Pending",
        )
        .delete(synchronize_session=False)
    )
    if deleted != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Food change request is no longer pending.",
        )
    commit_or_raise(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{request_id}/reject",
    response_model=FoodChangeRequestResponse,
    summary="Reject a coach food suggestion",
)
def reject_food_suggestion(
    request_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FoodChangeRequestResponse:
    _, suggestion = _get_owned_request(
        db,
        request_id,
        current_user.id,
    )
    now = _utcnow()
    suggestion_updated = (
        db.query(CoachSuggestion)
        .filter(
            CoachSuggestion.SuggestionID == suggestion.SuggestionID,
            CoachSuggestion.Status == "Pending",
        )
        .update(
            {
                CoachSuggestion.Status: "Rejected",
                CoachSuggestion.UpdatedAt: now,
            },
            synchronize_session=False,
        )
    )
    request_updated = (
        db.query(FoodChangeRequest)
        .filter(
            FoodChangeRequest.RequestID == request_id,
            FoodChangeRequest.UserID == current_user.id,
            FoodChangeRequest.Status == "Reviewed",
        )
        .update(
            {
                FoodChangeRequest.Status: "Rejected",
                FoodChangeRequest.UpdatedAt: now,
            },
            synchronize_session=False,
        )
    )
    if suggestion_updated != 1 or request_updated != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The request or suggestion has changed; reload and try again.",
        )
    commit_or_raise(db)
    db.expire_all()
    return _get_request_response(db, request_id)
