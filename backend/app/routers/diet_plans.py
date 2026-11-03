from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.database import get_db, utc_now
from app.models import DietPlan, FoodItem, Meal, MealItem, NutritionSettings, User
from app.schemas.diet_plan import (
    DietPlanCreate,
    DietPlanUpdate,
    GenerateDietPlanInput,
)
from app.security import current_user
from app.services.transactions import commit_or_raise

router = APIRouter(prefix="/api/v1/diet-plans", tags=["Diet plans"])
MEAL_CATEGORIES = {
    "Breakfast": "Breakfast",
    "Lunch": "Lunch",
    "Dinner": "Dinner",
    "Snack": "Snacks",
}
MEAL_CALORIE_SHARES = {
    "Breakfast": 0.25,
    "Lunch": 0.30,
    "Snack": 0.15,
    "Dinner": 0.30,
}


def _plan_payload(db: Session, plan: DietPlan) -> dict:
    meals = list(
        db.scalars(
            select(Meal)
            .where(Meal.PlanID == plan.PlanID, Meal.UserID == plan.UserID)
            .order_by(Meal.MealDate, Meal.MealType, Meal.MealID)
        ).all()
    )
    items = list(
        db.execute(
            select(MealItem, FoodItem)
            .join(FoodItem, FoodItem.FoodID == MealItem.FoodID)
            .join(Meal, Meal.MealID == MealItem.MealID)
            .where(Meal.PlanID == plan.PlanID, Meal.UserID == plan.UserID)
            .order_by(Meal.MealID, MealItem.MealItemID)
        ).all()
    )
    items_by_meal: dict[int, list[dict]] = {meal.MealID: [] for meal in meals}
    for item, food in items:
        items_by_meal[item.MealID].append(
            {
                "MealItemID": item.MealItemID,
                "FoodID": item.FoodID,
                "Quantity": item.Quantity,
                "ServingUnit": item.ServingUnit,
                "Food": {
                    "FoodID": food.FoodID,
                    "CatalogID": food.CatalogID,
                    "FoodName": food.FoodName,
                    "Category": food.Category,
                    "Calories": food.Calories,
                    "Protein": food.Protein,
                    "Carbs": food.Carbs,
                    "Fat": food.Fat,
                    "Fiber": food.Fiber,
                    "ServingSize": food.ServingSize,
                },
            }
        )
    return {
        "PlanID": plan.PlanID,
        "PlanName": plan.PlanName,
        "StartDate": plan.StartDate,
        "EndDate": plan.EndDate,
        "Status": plan.Status,
        "CreatedAt": plan.CreatedAt,
        "UpdatedAt": plan.UpdatedAt,
        "Meals": [
            {
                "MealID": meal.MealID,
                "UserID": meal.UserID,
                "PlanID": meal.PlanID,
                "MealDate": meal.MealDate,
                "MealType": meal.MealType,
                "Notes": meal.Notes,
                "Items": items_by_meal[meal.MealID],
            }
            for meal in meals
        ],
    }


def _owned_plan(db: Session, plan_id: int, user_id: int) -> DietPlan:
    plan = db.scalar(
        select(DietPlan).where(
            DietPlan.PlanID == plan_id,
            DietPlan.UserID == user_id,
        )
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Diet plan not found.")
    return plan


@router.post("/generate")
def generate_diet_plan(
    payload: GenerateDietPlanInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    if not user.profile or not user.profile.goal:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete onboarding and set a weight goal before generating a meal plan.",
        )
    profile = user.profile
    if (profile.allergies or "").strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A meal plan cannot be generated safely because food ingredient and allergen data is not available in the catalog.",
        )
    preference = (profile.dietary_preference or "").strip().casefold()
    if "vegan" in preference:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A vegan meal plan cannot be verified because ingredient-level food data is not available in the catalog.",
        )

    foods = list(
        db.scalars(
            select(FoodItem)
            .where(FoodItem.IsActive == true())
            .order_by(FoodItem.FoodName, FoodItem.FoodID)
        ).all()
    )
    foods_by_category: dict[str, list[FoodItem]] = {
        category: [
            food for food in foods
            if food.Category == category
            and float(food.Calories) > 0
            and not (
                ("vegetarian" in preference or "pescatarian" in preference)
                and "chicken" in food.FoodName.casefold()
            )
        ]
        for category in set(MEAL_CATEGORIES.values())
    }
    missing_categories = [
        category for category, candidates in foods_by_category.items() if not candidates
    ]
    if missing_categories:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The active food catalog is missing one or more meal categories required to generate a complete plan.",
        )

    settings = db.scalar(
        select(NutritionSettings).where(NutritionSettings.user_id == user.id)
    )
    calorie_goal = settings.calorie_goal if settings else 2000
    end_date = payload.StartDate + timedelta(days=payload.Days - 1)
    meals: list[dict] = []
    for day_index in range(payload.Days):
        meal_date = payload.StartDate + timedelta(days=day_index)
        for meal_type, category in MEAL_CATEGORIES.items():
            target_calories = calorie_goal * MEAL_CALORIE_SHARES[meal_type]
            ranked_foods = sorted(
                foods_by_category[category],
                key=lambda food: (
                    abs(float(food.Calories) - target_calories),
                    food.FoodID,
                ),
            )
            food = ranked_foods[day_index % min(4, len(ranked_foods))]
            quantity = min(
                Decimal("50.00"),
                max(
                    Decimal("0.01"),
                    Decimal(str(round(target_calories / float(food.Calories), 2))),
                ),
            )
            meals.append(
                {
                    "MealDate": meal_date,
                    "MealType": meal_type,
                    "Notes": "Generated from active catalog nutrition values.",
                    "Items": [
                        {
                            "FoodID": food.FoodID,
                            "Quantity": quantity,
                            "ServingUnit": food.ServingSize or "serving",
                            "Food": {
                                "FoodID": food.FoodID,
                                "CatalogID": food.CatalogID,
                                "FoodName": food.FoodName,
                                "Category": food.Category,
                                "Calories": food.Calories,
                                "Protein": food.Protein,
                                "Carbs": food.Carbs,
                                "Fat": food.Fat,
                                "ServingSize": food.ServingSize,
                            },
                        }
                    ],
                }
            )

    return {
        "PlanName": f"{profile.dietary_preference} meal plan",
        "StartDate": payload.StartDate,
        "EndDate": end_date,
        "Status": "Active",
        "DailyCalorieGoal": calorie_goal,
        "GoalType": profile.goal.goal_type,
        "Meals": meals,
        "Notice": "Plan quantities use active catalog serving values. Nutrition is estimated; review the meals before following this plan.",
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_diet_plan(
    payload: DietPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    food_ids = {item.FoodID for meal in payload.Meals for item in meal.Items}
    active_food_ids = set(
        db.scalars(
            select(FoodItem.FoodID).where(
                FoodItem.FoodID.in_(food_ids),
                FoodItem.IsActive == true(),
            )
        ).all()
    )
    if active_food_ids != food_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Every plan item must reference an active food catalog record.",
        )

    plan = DietPlan(
        UserID=user.id,
        PlanName=payload.PlanName.strip(),
        StartDate=payload.StartDate,
        EndDate=payload.EndDate,
        Status="Active",
    )
    db.add(plan)
    db.flush()
    for meal_payload in payload.Meals:
        meal = Meal(
            UserID=user.id,
            PlanID=plan.PlanID,
            MealDate=meal_payload.MealDate,
            MealType=meal_payload.MealType,
            Notes=meal_payload.Notes,
        )
        db.add(meal)
        db.flush()
        db.add_all(
            [
                MealItem(
                    MealID=meal.MealID,
                    FoodID=item.FoodID,
                    Quantity=item.Quantity,
                    ServingUnit=item.ServingUnit,
                )
                for item in meal_payload.Items
            ]
        )
    commit_or_raise(db)
    db.refresh(plan)
    return _plan_payload(db, plan)


@router.get("/")
def list_diet_plans(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[dict]:
    plans = list(
        db.scalars(
            select(DietPlan)
            .where(DietPlan.UserID == user.id)
            .order_by(DietPlan.CreatedAt.desc(), DietPlan.PlanID.desc())
        ).all()
    )
    return [_plan_payload(db, plan) for plan in plans]


@router.get("/{plan_id}")
def get_diet_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    return _plan_payload(db, _owned_plan(db, plan_id, user.id))


@router.put("/{plan_id}")
def update_diet_plan(
    plan_id: int,
    payload: DietPlanUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    plan = _owned_plan(db, plan_id, user.id)
    values = payload.model_dump(exclude_unset=True)
    if "PlanName" in values:
        plan.PlanName = values["PlanName"].strip()
    if "Status" in values:
        plan.Status = values["Status"]
    plan.UpdatedAt = utc_now()
    commit_or_raise(db)
    db.refresh(plan)
    return _plan_payload(db, plan)
