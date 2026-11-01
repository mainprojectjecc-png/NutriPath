from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import true
from sqlalchemy.orm import Session

from app.auth import verify_access_token
from app.database import get_db
from app.models.diet_plan import DietPlan
from app.models.food_change_request import FoodChangeRequest
from app.models.food_item import FoodItem
from app.models.meal import Meal
from app.models.meal_item import MealItem
from app.schemas.food_item import FoodItemResponse
from app.schemas.meal import (
    MealCreate,
    MealItemCreate,
    MealItemResponse,
    MealItemUpdate,
    MealResponse,
)
from app.services.transactions import commit_or_raise

router = APIRouter(prefix="/api/v1/meals", tags=["Meals"])


def _get_owned_meal(db: Session, meal_id: int, user_id: int) -> Meal:
    meal = (
        db.query(Meal)
        .filter(Meal.MealID == meal_id, Meal.UserID == user_id)
        .first()
    )
    if meal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found",
        )
    return meal


def _meal_item_response(item: MealItem, food: FoodItem) -> MealItemResponse:
    return MealItemResponse(
        MealItemID=item.MealItemID,
        FoodID=item.FoodID,
        Quantity=item.Quantity,
        ServingUnit=item.ServingUnit,
        Food=FoodItemResponse.model_validate(food),
    )


def _meal_responses(db: Session, meals: list[Meal]) -> list[MealResponse]:
    if not meals:
        return []

    meal_ids = [meal.MealID for meal in meals]
    item_rows = (
        db.query(MealItem, FoodItem)
        .join(FoodItem, FoodItem.FoodID == MealItem.FoodID)
        .filter(MealItem.MealID.in_(meal_ids))
        .order_by(MealItem.MealID.asc(), MealItem.MealItemID.asc())
        .all()
    )
    items_by_meal: dict[int, list[MealItemResponse]] = {
        meal_id: [] for meal_id in meal_ids
    }
    for item, food in item_rows:
        items_by_meal[item.MealID].append(_meal_item_response(item, food))

    return [
        MealResponse(
            MealID=meal.MealID,
            UserID=meal.UserID,
            PlanID=meal.PlanID,
            MealDate=meal.MealDate,
            MealType=meal.MealType,
            Notes=meal.Notes,
            Items=items_by_meal[meal.MealID],
        )
        for meal in meals
    ]


@router.post(
    "/",
    response_model=MealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a meal",
)
def create_meal(
    meal_data: MealCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> MealResponse:
    user_id = current_user["user_id"]
    if meal_data.PlanID is not None:
        plan = (
            db.query(DietPlan)
            .filter(
                DietPlan.PlanID == meal_data.PlanID,
                DietPlan.UserID == user_id,
            )
            .first()
        )
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet plan not found",
            )

    meal = Meal(
        UserID=user_id,
        PlanID=meal_data.PlanID,
        MealDate=meal_data.MealDate,
        MealType=meal_data.MealType,
        Notes=meal_data.Notes,
    )
    db.add(meal)
    commit_or_raise(db)
    db.refresh(meal)
    return _meal_responses(db, [meal])[0]


@router.get(
    "/",
    response_model=list[MealResponse],
    summary="List meal history",
)
def get_meal_history(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> list[MealResponse]:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date",
        )

    meals_query = db.query(Meal).filter(Meal.UserID == current_user["user_id"])
    if start_date is not None:
        meals_query = meals_query.filter(Meal.MealDate >= start_date)
    if end_date is not None:
        meals_query = meals_query.filter(Meal.MealDate <= end_date)
    meals = (
        meals_query.order_by(
            Meal.MealDate.asc(),
            Meal.MealType.asc(),
            Meal.MealID.asc(),
        )
        .all()
    )
    return _meal_responses(db, meals)


@router.get(
    "/{date}",
    response_model=list[MealResponse],
    summary="Get meals for a date",
)
def get_meals_for_date(
    date: date,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> list[MealResponse]:
    meals = (
        db.query(Meal)
        .filter(
            Meal.UserID == current_user["user_id"],
            Meal.MealDate == date,
        )
        .order_by(Meal.MealType.asc(), Meal.MealID.asc())
        .all()
    )
    return _meal_responses(db, meals)


@router.post(
    "/{meal_id}/items",
    response_model=MealItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a food to a meal",
)
def add_meal_item(
    meal_id: Annotated[int, Path(gt=0)],
    item_data: MealItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> MealItemResponse:
    _get_owned_meal(db, meal_id, current_user["user_id"])
    food = (
        db.query(FoodItem)
        .filter(
            FoodItem.FoodID == item_data.FoodID,
            FoodItem.IsActive == true(),
        )
        .first()
    )
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active food item not found",
        )

    item = MealItem(
        MealID=meal_id,
        FoodID=item_data.FoodID,
        Quantity=item_data.Quantity,
        ServingUnit=item_data.ServingUnit,
    )
    db.add(item)
    commit_or_raise(db)
    db.refresh(item)
    return _meal_item_response(item, food)


@router.put(
    "/{meal_id}/items/{meal_item_id}",
    response_model=MealItemResponse,
    summary="Update a meal item",
)
def update_meal_item(
    meal_id: Annotated[int, Path(gt=0)],
    meal_item_id: Annotated[int, Path(gt=0)],
    item_data: MealItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> MealItemResponse:
    _get_owned_meal(db, meal_id, current_user["user_id"])
    item = (
        db.query(MealItem)
        .filter(
            MealItem.MealID == meal_id,
            MealItem.MealItemID == meal_item_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal item not found",
        )

    if item_data.Quantity is not None:
        item.Quantity = item_data.Quantity
    if item_data.ServingUnit is not None:
        item.ServingUnit = item_data.ServingUnit
    commit_or_raise(db)
    db.refresh(item)

    food = db.query(FoodItem).filter(FoodItem.FoodID == item.FoodID).first()
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found",
        )
    return _meal_item_response(item, food)


@router.delete(
    "/{meal_id}/items/{meal_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a meal item",
)
def delete_meal_item(
    meal_id: Annotated[int, Path(gt=0)],
    meal_item_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> Response:
    _get_owned_meal(db, meal_id, current_user["user_id"])
    item = (
        db.query(MealItem)
        .filter(
            MealItem.MealID == meal_id,
            MealItem.MealItemID == meal_item_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal item not found",
        )

    request = (
        db.query(FoodChangeRequest.RequestID)
        .filter(FoodChangeRequest.MealItemID == meal_item_id)
        .first()
    )
    if request is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meal item has a food change request and cannot be deleted.",
        )

    db.delete(item)
    commit_or_raise(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{meal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a meal",
)
def delete_meal(
    meal_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token),
) -> Response:
    meal = _get_owned_meal(db, meal_id, current_user["user_id"])
    request = (
        db.query(FoodChangeRequest.RequestID)
        .join(MealItem, MealItem.MealItemID == FoodChangeRequest.MealItemID)
        .filter(MealItem.MealID == meal_id)
        .first()
    )
    if request is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meal has food change requests and cannot be deleted.",
        )

    db.query(MealItem).filter(MealItem.MealID == meal_id).delete(
        synchronize_session=False
    )
    db.delete(meal)
    commit_or_raise(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
