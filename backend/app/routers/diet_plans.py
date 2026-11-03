import hashlib
import json
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.database import get_db, utc_now
from app.models import DietPlan, FoodItem, Meal, MealItem, NutritionSettings, User
from app.models.food_item import FoodSafetyMetadata
from app.schemas.diet_plan import (
    DietPlanCreate,
    DietPlanUpdate,
    GenerateDietPlanInput,
)
from app.security import current_user
from app.services.transactions import commit_or_raise
from app.services.food_safety import (
    is_allergy_safe,
    is_diet_eligible,
    is_food_avoided,
    metadata_is_complete,
    restrictions_match_catalog,
)

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
NUTRIENT_FIELDS = ("Calories", "Protein", "Carbs", "Fat", "Fiber")


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
    nutrition_by_meal = {
        meal.MealID: {field: 0.0 for field in NUTRIENT_FIELDS}
        for meal in meals
    }
    food_ids = set()
    for item, food in items:
        food_ids.add(food.FoodID)
        quantity = float(item.Quantity)
        for field in NUTRIENT_FIELDS:
            nutrition_by_meal[item.MealID][field] += float(
                getattr(food, field) or 0
            ) * quantity
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
                    "SafetyStatus": "unknown",
                },
            }
        )
    metadata_rows = list(
        db.scalars(
            select(FoodSafetyMetadata).where(
                FoodSafetyMetadata.FoodID.in_(food_ids)
            )
        ).all()
    ) if food_ids else []
    verified_food_ids = {
        metadata.FoodID
        for metadata in metadata_rows
        if metadata_is_complete(metadata)
    }
    for meal_items in items_by_meal.values():
        for item in meal_items:
            item["Food"]["SafetyStatus"] = (
                "verified" if item["FoodID"] in verified_food_ids else "unknown"
            )
    for nutrition in nutrition_by_meal.values():
        for field in NUTRIENT_FIELDS:
            nutrition[field] = round(nutrition[field], 2)
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
                "Nutrition": nutrition_by_meal[meal.MealID],
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


def _profile_restrictions(profile) -> tuple[list[str | None], list[str | None]]:
    allergy_restrictions = [profile.allergies, profile.intolerances]
    food_avoidance_restrictions = [
        profile.foods_to_avoid,
        profile.other_dietary_restrictions,
    ]
    return allergy_restrictions, food_avoidance_restrictions


def _food_allowed(food, metadata, preference, allergy_restrictions, avoidance_restrictions):
    return (
        is_diet_eligible(metadata, preference)
        and is_allergy_safe(metadata, allergy_restrictions)
        and not is_food_avoided(food.FoodName, metadata, avoidance_restrictions)
    )


def _scaled_nutrients(food, quantity: Decimal) -> dict[str, float]:
    return {
        field: round(float(getattr(food, field) or 0) * float(quantity), 2)
        for field in NUTRIENT_FIELDS
    }


@router.post("/generate")
def generate_diet_plan(
    payload: GenerateDietPlanInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:

    if not user.profile or not user.profile.goal:
        raise HTTPException(
            status_code=409,
            detail="Complete onboarding and set a weight goal before generating a meal plan.",
        )

    profile = user.profile

    preference = (
        profile.dietary_preference or "No preference"
    ).strip().casefold()
    if preference == "balanced":
        preference = "no preference"

    supported_preferences = {
        "no preference",
        "vegetarian",
        "vegan",
        "pescatarian",
        "eggetarian",
        "omnivore",
        "other",
    }

    if preference not in supported_preferences:
        raise HTTPException(
            status_code=422,
            detail="Unsupported dietary preference.",
        )

    if preference == "other":
        custom_restrictions = [
            profile.other_dietary_restrictions,
            profile.foods_to_avoid,
        ]
        if not any((value or "").strip() for value in custom_restrictions):
            raise HTTPException(
                status_code=422,
                detail=(
                    "For the Other dietary preference, list the specific "
                    "ingredients or food groups you avoid in your profile."
                ),
            )

    settings = db.scalar(
        select(NutritionSettings).where(
            NutritionSettings.user_id == user.id
        )
    )

    calorie_goal = settings.calorie_goal if settings else 2000

    foods = list(
        db.scalars(
            select(FoodItem)
            .where(FoodItem.IsActive == true())
            .order_by(FoodItem.FoodName, FoodItem.FoodID)
        ).all()
    )

    metadata_rows = list(
        db.scalars(
            select(FoodSafetyMetadata).where(
                FoodSafetyMetadata.FoodID.in_(
                    [food.FoodID for food in foods]
                )
            )
        ).all()
    )

    metadata_by_id = {
        item.FoodID: item
        for item in metadata_rows
    }

    allergy_restrictions, avoidance_restrictions = _profile_restrictions(profile)
    if preference == "other" and not restrictions_match_catalog(
        avoidance_restrictions,
        [
            " ".join(
                value
                for value in (
                    food.FoodName,
                    metadata_by_id.get(food.FoodID).Ingredients
                    if metadata_by_id.get(food.FoodID) else "",
                    metadata_by_id.get(food.FoodID).Allergens
                    if metadata_by_id.get(food.FoodID) else "",
                )
                if value
            )
            for food in foods
            if metadata_is_complete(metadata_by_id.get(food.FoodID))
        ],
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "The catalog cannot verify the custom restrictions in your "
                "profile. Add verified ingredient data for those restrictions "
                "before generating a plan."
            ),
        )

    foods_by_category = {}
    unknown_food_ids = []

    for category in set(MEAL_CATEGORIES.values()):

        candidates = []

        for food in foods:

            if food.Category != category:
                continue

            if float(food.Calories) <= 0:
                continue

            metadata = metadata_by_id.get(food.FoodID)

            if not metadata_is_complete(metadata):
                unknown_food_ids.append(food.FoodID)

            if not _food_allowed(
                food,
                metadata,
                preference,
                allergy_restrictions,
                avoidance_restrictions,
            ):
                continue

            candidates.append(food)

        foods_by_category[category] = candidates

    missing_categories = [
        category
        for category, candidates in foods_by_category.items()
        if not candidates
    ]

    if missing_categories:
        missing_labels = ", ".join(sorted(missing_categories))
        unknown_detail = (
            f" Food IDs with missing or unverified safety metadata: "
            f"{', '.join(map(str, sorted(set(unknown_food_ids))[:20]))}."
            if unknown_food_ids
            else ""
        )
        raise HTTPException(
            status_code=409,
            detail=(
                "There are not enough verified, suitable foods for "
                f"{missing_labels}. Add reliable ingredient, allergen, "
                "dietary-classification, and cross-contact catalog data; "
                "no unsafe substitute was selected."
                f"{unknown_detail}"
            ),
        )

    end_date = payload.StartDate + timedelta(
        days=payload.Days - 1
    )

    meals = []
    daily_nutrition = []

    for day_index in range(payload.Days):

        meal_date = payload.StartDate + timedelta(
            days=day_index
        )

        for meal_type, category in MEAL_CATEGORIES.items():

            target_calories = (
                float(calorie_goal)
                * MEAL_CALORIE_SHARES[meal_type]
            )

            ranked_foods = sorted(
                foods_by_category[category],
                key=lambda food: (
                    abs(float(food.Calories) - target_calories),
                    food.FoodID,
                ),
            )

            food = ranked_foods[
                day_index % len(ranked_foods)
            ]

            quantity = (
                Decimal(str(target_calories)) / Decimal(str(food.Calories))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            quantity = min(Decimal("50.00"), max(Decimal("0.01"), quantity))
            nutrients = _scaled_nutrients(food, quantity)

            meals.append({
                "MealDate": meal_date,
                "MealType": meal_type,
                "Notes": (
                    "Generated using active catalog nutrition "
                    "and applicable verified food-safety metadata."
                ),
                "Items": [{
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
                        "Fiber": food.Fiber,
                        "ServingSize": food.ServingSize,
                        "SafetyStatus": (
                            "verified"
                            if metadata_is_complete(metadata_by_id.get(food.FoodID))
                            else "unknown"
                        ),
                    },
                }],
                "Nutrition": nutrients,
            })

        daily_meals = [
            meal for meal in meals if meal["MealDate"] == meal_date
        ]
        daily_nutrition.append(
            {
                "Date": meal_date,
                **{
                    field: round(
                        sum(meal["Nutrition"][field] for meal in daily_meals),
                        2,
                    )
                    for field in NUTRIENT_FIELDS
                },
            }
        )

    unknown_selected = any(
        item["Food"]["SafetyStatus"] == "unknown"
        for meal in meals
        for item in meal["Items"]
    )
    notice = (
        "Some selected foods have unknown safety metadata. Ingredient and "
        "allergen safety is not verified for those foods."
        if unknown_selected
        else "All selected foods have verified safety metadata."
    )

    return {
        "PlanName": f"{profile.dietary_preference or 'No preference'} meal plan",
        "StartDate": payload.StartDate,
        "EndDate": end_date,
        "Status": "Active",
        "DailyCalorieGoal": calorie_goal,
        "GoalType": profile.goal.goal_type,
        "Meals": meals,
        "DailyNutrition": daily_nutrition,
        "Notice": (
            f"{notice} Portions use saved catalog nutrition values. "
            "Review the plan before following it."
        ),
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_diet_plan(
    payload: DietPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict:
    food_ids = {item.FoodID for meal in payload.Meals for item in meal.Items}
    foods = list(
        db.scalars(
            select(FoodItem).where(
                FoodItem.FoodID.in_(food_ids),
                FoodItem.IsActive == true(),
            )
        ).all()
    )
    foods_by_id = {food.FoodID: food for food in foods}
    if set(foods_by_id) != food_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Every plan item must reference an active food catalog record.",
        )

    metadata_rows = list(
        db.scalars(
            select(FoodSafetyMetadata).where(
                FoodSafetyMetadata.FoodID.in_(food_ids)
            )
        ).all()
    )
    metadata_by_id = {item.FoodID: item for item in metadata_rows}
    profile = user.profile
    preference = (
        (profile.dietary_preference or "No preference") if profile else "No preference"
    ).strip().casefold()
    if preference not in {
        "",
        "no preference",
        "vegetarian",
        "vegan",
        "eggetarian",
        "pescatarian",
        "omnivore",
        "other",
    }:
        raise HTTPException(status_code=422, detail="Unsupported dietary preference.")
    if preference == "other" and not any(
        (value or "").strip()
        for value in (
            profile.other_dietary_restrictions,
            profile.foods_to_avoid,
        )
    ):
        raise HTTPException(
            status_code=422,
            detail="Specify your Other dietary restrictions before saving a plan.",
        )
    allergy_restrictions, avoidance_restrictions = (
        _profile_restrictions(profile)
        if profile
        else ([], [])
    )
    if preference == "other" and not restrictions_match_catalog(
        avoidance_restrictions,
        [
            " ".join(
                value
                for value in (
                    food.FoodName,
                    metadata_by_id[food.FoodID].Ingredients,
                    metadata_by_id[food.FoodID].Allergens,
                )
                if value
            )
            for food in foods
            if food.FoodID in metadata_by_id
            and metadata_is_complete(metadata_by_id[food.FoodID])
        ],
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "The catalog cannot verify the custom restrictions in your "
                "profile. Add verified ingredient data for those restrictions "
                "before saving a plan."
            ),
        )
    category_by_meal_type = {
        "Breakfast": "Breakfast",
        "Lunch": "Lunch",
        "Dinner": "Dinner",
        "Snack": "Snacks",
    }
    for meal_payload in payload.Meals:
        expected_category = category_by_meal_type[meal_payload.MealType]
        for item in meal_payload.Items:
            food = foods_by_id[item.FoodID]
            metadata = metadata_by_id.get(item.FoodID)
            if food.Category != expected_category:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{food.FoodName} is not categorized for "
                        f"{meal_payload.MealType.lower()}."
                    ),
                )
            if not _food_allowed(
                food,
                metadata,
                preference,
                allergy_restrictions,
                avoidance_restrictions,
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{food.FoodName} cannot be verified as suitable "
                        "for your dietary preference and restrictions."
                    ),
                )

    canonical_payload = payload.model_dump(mode="json", exclude={"IdempotencyKey"})
    idempotency_key = hashlib.sha256(
        f"{user.id}:{json.dumps(canonical_payload, sort_keys=True)}".encode("utf-8")
    ).hexdigest()
    existing = db.scalar(
        select(DietPlan).where(
            DietPlan.UserID == user.id,
            DietPlan.IdempotencyKey == idempotency_key,
        )
    )
    if existing is not None:
        return _plan_payload(db, existing)

    plan = DietPlan(
        UserID=user.id,
        PlanName=payload.PlanName.strip(),
        IdempotencyKey=idempotency_key,
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
    try:
        commit_or_raise(db)
    except HTTPException:
        existing = db.scalar(
            select(DietPlan).where(
                DietPlan.UserID == user.id,
                DietPlan.IdempotencyKey == idempotency_key,
            )
        )
        if existing is None:
            raise
        return _plan_payload(db, existing)
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
