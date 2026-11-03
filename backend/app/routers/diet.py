
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from diet_engine import (
    calculate_bmi,
    calculate_daily_calories,
    calculate_weight_change,
    generate_monthly_journey,
    generate_daily_meals,
    suggest_food_replacements,
)

router = APIRouter(
    prefix="/api/v1/diet",
    tags=["Diet Engine"],
)


# Request models

class BMIRequest(BaseModel):
    weight_kg: float
    height_cm: float


class CalorieRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    gender: str
    activity_factor: float = 1.2


class WeightChangeRequest(BaseModel):
    current_weight: float
    target_weight: float


class JourneyRequest(BaseModel):
    current_weight: float
    target_weight: float
    start_date: str
    duration_months: int = 3


class MealRequest(BaseModel):
    user_preferences: dict
    meal_date: str


class FoodReplacementRequest(BaseModel):
    food_to_replace: str
    preferences: dict


# API endpoints

@router.post("/bmi")
def get_bmi(data: BMIRequest):
    try:
        return calculate_bmi(data.weight_kg, data.height_cm)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/calories")
def get_calories(data: CalorieRequest):
    try:
        return calculate_daily_calories(
            data.weight_kg,
            data.height_cm,
            data.age,
            data.gender,
            data.activity_factor,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/weight-change")
def get_weight_change(data: WeightChangeRequest):
    try:
        return calculate_weight_change(
            data.current_weight,
            data.target_weight,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/journey")
def get_monthly_journey(data: JourneyRequest):
    try:
        return generate_monthly_journey(
            data.current_weight,
            data.target_weight,
            data.start_date,
            data.duration_months,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/meals")
def get_daily_meals(data: MealRequest):
    try:
        return generate_daily_meals(
            data.user_preferences,
            data.meal_date,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/food-replacements")
def get_food_replacements(data: FoodReplacementRequest):
    try:
        return suggest_food_replacements(
            data.food_to_replace,
            data.preferences,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
