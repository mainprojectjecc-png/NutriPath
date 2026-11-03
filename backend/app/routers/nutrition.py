from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FoodChangeRequest, NutritionLog, NutritionSettings, User, WaterLog
from app.schemas.schemas import NutritionEntryInput, NutritionSettingsInput, WaterEntryInput
from app.security import current_user
from app.services.food_emojis import (
    DEFAULT_FOOD_EMOJI,
    get_canonical_food_emoji,
    is_corrupted_emoji,
)

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


def _meal_view(entry: NutritionLog) -> dict:
    emoji = get_canonical_food_emoji(entry.food_id) or entry.emoji
    if is_corrupted_emoji(emoji):
        emoji = DEFAULT_FOOD_EMOJI
    return {
        "id": entry.id,
        "foodId": entry.food_id,
        "foodName": entry.food_name,
        "emoji": emoji,
        "mealType": entry.meal_type,
        "quantity": entry.quantity,
        "servingLabel": entry.serving_label,
        "servingGrams": entry.serving_grams,
        "calories": entry.calories,
        "protein": entry.protein,
        "carbs": entry.carbs,
        "fats": entry.fats,
        "date": entry.logged_on.isoformat(),
        "loggedAt": entry.created_at.isoformat(),
    }


def _water_view(entry: WaterLog) -> dict:
    return {
        "id": entry.id,
        "amount_ml": entry.amount_ml,
        "date": entry.logged_on.isoformat(),
        "logged_at": entry.created_at.isoformat(),
    }


def _nutrition_state(db: Session, user: User) -> dict:
    meals = db.scalars(
        select(NutritionLog)
        .where(NutritionLog.user_id == user.id)
        .order_by(NutritionLog.logged_on, NutritionLog.created_at, NutritionLog.id)
    ).all()
    water_entries = db.scalars(
        select(WaterLog)
        .where(WaterLog.user_id == user.id)
        .order_by(WaterLog.logged_on, WaterLog.created_at, WaterLog.id)
    ).all()
    water_by_date: dict[str, int] = defaultdict(int)
    for entry in water_entries:
        water_by_date[entry.logged_on.isoformat()] += entry.amount_ml
    settings = db.scalar(select(NutritionSettings).where(NutritionSettings.user_id == user.id))
    return {
        "meals": [_meal_view(entry) for entry in meals],
        "waterEntries": [_water_view(entry) for entry in water_entries],
        "waterByDate": dict(water_by_date),
        "calorieGoal": settings.calorie_goal if settings else 2000,
        "waterGoal": settings.water_goal if settings else 2500,
    }


@router.get("")
def get_nutrition(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _nutrition_state(db, user)


@router.post("/meals", status_code=status.HTTP_201_CREATED)
def add_nutrition_entry(payload: NutritionEntryInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    values = payload.model_dump(exclude={"date"})
    entry = NutritionLog(user_id=user.id, logged_on=payload.date, **values)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _meal_view(entry)


@router.delete("/meals/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nutrition_entry(entry_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    entry = db.scalar(select(NutritionLog).where(NutritionLog.id == entry_id, NutritionLog.user_id == user.id))
    if not entry:
        raise HTTPException(status_code=404, detail="Food entry not found.")
    has_food_change_request = db.scalar(
        select(FoodChangeRequest.RequestID)
        .where(FoodChangeRequest.NutritionLogID == entry.id)
        .limit(1)
    )
    if has_food_change_request is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This meal cannot be deleted because it has an associated food-change request.",
        )
    db.delete(entry)
    db.commit()
    return None


@router.post("/water", status_code=status.HTTP_201_CREATED)
def add_water_entry(payload: WaterEntryInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    entry = WaterLog(user_id=user.id, amount_ml=payload.amount_ml, logged_on=payload.date)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _water_view(entry)


@router.put("/water/{entry_id}")
def update_water_entry(
    entry_id: int,
    payload: WaterEntryInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    entry = db.scalar(
        select(WaterLog).where(
            WaterLog.id == entry_id,
            WaterLog.user_id == user.id,
        )
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Water entry not found.")
    entry.amount_ml = payload.amount_ml
    entry.logged_on = payload.date
    db.commit()
    db.refresh(entry)
    return _water_view(entry)


@router.delete("/water/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_water_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    entry = db.scalar(
        select(WaterLog).where(
            WaterLog.id == entry_id,
            WaterLog.user_id == user.id,
        )
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Water entry not found.")
    db.delete(entry)
    db.commit()
    return None


@router.put("/settings")
def update_nutrition_settings(payload: NutritionSettingsInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    settings = db.scalar(select(NutritionSettings).where(NutritionSettings.user_id == user.id))
    if settings:
        settings.calorie_goal = payload.calorie_goal
        settings.water_goal = payload.water_goal
    else:
        settings = NutritionSettings(user_id=user.id, **payload.model_dump())
        db.add(settings)
    db.commit()
    return {"calorieGoal": settings.calorie_goal, "waterGoal": settings.water_goal}
