import sys
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database import Base, get_db
from app.main import app
from app.models import DietPlan, FoodItem, FoodSafetyMetadata, User
from app.services.food_safety import is_allergy_safe


@pytest.fixture
def api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, session_factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def register_and_onboard(client, preference="No preference", **restrictions):
    registration = client.post(
        "/api/auth/register",
        json={
            "full_name": "Meal Planner Tester",
            "email": f"planner-{uuid4().hex}@example.com",
            "password": "secure-password-123",
        },
    )
    assert registration.status_code == 201, registration.text
    token = registration.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/onboarding",
        headers=headers,
        json={
            "full_name": "Meal Planner Tester",
            "age": 31,
            "height_cm": 170,
            "gender": None,
            "activity_level": "light",
            "dietary_preference": preference,
            "allergies": restrictions.get("allergies", ""),
            "intolerances": restrictions.get("intolerances", ""),
            "foods_to_avoid": restrictions.get("foods_to_avoid", ""),
            "other_dietary_restrictions": restrictions.get(
                "other_dietary_restrictions", ""
            ),
            "exercise_preferences": "",
            "daily_routine": "",
            "goal": {
                "goal_type": "weight_loss",
                "starting_weight_kg": 75,
                "target_weight_kg": 70,
                "duration_weeks": 12,
                "start_date": date.today().isoformat(),
            },
        },
    )
    assert response.status_code == 201, response.text
    return headers


def add_foods(session_factory, *, verified=True, include_meat=False, repeats=1):
    categories = (
        ("Breakfast", 400),
        ("Lunch", 400),
        ("Dinner", 400),
        ("Snacks", 200),
    )
    with session_factory() as db:
        created = []
        for category, calories in categories:
            for number in range(repeats):
                food = FoodItem(
                    CatalogID=f"test-{category}-{number}",
                    FoodName=f"{category} plant {number}",
                    Category=category,
                    Calories=calories,
                    Protein=12,
                    Carbs=45,
                    Fat=8,
                    Fiber=6,
                    ServingSize="1 serving",
                    IsActive=True,
                )
                db.add(food)
                db.flush()
                if verified:
                    db.add(
                        FoodSafetyMetadata(
                            FoodID=food.FoodID,
                            Ingredients="rice, lentils, vegetables",
                            Allergens="",
                            DietaryClassifications='["vegetarian", "vegan"]',
                            AnimalDerivedIngredients="",
                            CrossContactWarnings="",
                            VerificationSource="Test fixture",
                            VerifiedAt=datetime.now(),
                            IsVerified=True,
                            IsVegetarian=True,
                            IsVegan=True,
                            ContainsEgg=False,
                            ContainsDairy=False,
                            ContainsHoney=False,
                            ContainsFish=False,
                            ContainsSeafood=False,
                            ContainsMeat=False,
                        )
                    )
                created.append(food)
        if include_meat:
            meat = FoodItem(
                CatalogID="test-chicken",
                FoodName="Chicken curry",
                Category="Dinner",
                Calories=500,
                Protein=30,
                Carbs=12,
                Fat=18,
                Fiber=2,
                ServingSize="1 bowl",
                IsActive=True,
            )
            db.add(meat)
            db.flush()
            db.add(
                FoodSafetyMetadata(
                    FoodID=meat.FoodID,
                    Ingredients="chicken, tomato, spices",
                    Allergens="",
                    DietaryClassifications='["omnivore"]',
                    AnimalDerivedIngredients="chicken",
                    CrossContactWarnings="",
                    VerificationSource="Test fixture",
                    VerifiedAt=datetime.now(),
                    IsVerified=True,
                    IsVegetarian=False,
                    IsVegan=False,
                    ContainsEgg=False,
                    ContainsDairy=False,
                    ContainsHoney=False,
                    ContainsFish=False,
                    ContainsSeafood=False,
                    ContainsMeat=True,
                )
            )
            created.append(meat)
        db.commit()
        return {food.FoodName: food.FoodID for food in created}


def generate(client, headers, days=1):
    response = client.post(
        "/api/v1/diet-plans/generate",
        headers=headers,
        json={"StartDate": date.today().isoformat(), "Days": days},
    )
    return response


@pytest.mark.parametrize(
    ("preference", "metadata", "expected_status"),
    [
        ("No preference", False, 200),
        ("Vegetarian", True, 200),
        ("Vegan", True, 200),
        ("Eggetarian", True, 200),
        ("Pescatarian", True, 200),
        ("Omnivore", False, 200),
        ("Other", True, 200),
    ],
)
def test_supported_dietary_preferences_are_explicit_and_conservative(
    api, preference, metadata, expected_status
):
    client, session_factory = api
    restrictions = {"other_dietary_restrictions": "chicken"} if preference == "Other" else {}
    headers = register_and_onboard(client, preference, **restrictions)
    add_foods(session_factory, verified=metadata, include_meat=True)
    response = generate(client, headers)
    assert response.status_code == expected_status, response.text
    if expected_status == 200:
        assert len(response.json()["Meals"]) == 4
        assert all(len(meal["Items"]) > 0 for meal in response.json()["Meals"])
        if preference in {"Vegetarian", "Vegan", "Eggetarian", "Pescatarian"}:
            assert all(
                item["Food"]["SafetyStatus"] == "verified"
                for meal in response.json()["Meals"]
                for item in meal["Items"]
            )
            if preference != "Pescatarian":
                assert all(
                    "chicken" not in item["Food"]["FoodName"].casefold()
                    for meal in response.json()["Meals"]
                    for item in meal["Items"]
                )


def test_no_preference_with_allergy_fails_closed_for_unknown_catalog_food(api):
    client, session_factory = api
    headers = register_and_onboard(client, allergies="Peanuts")
    food_ids = add_foods(session_factory, verified=False)
    response = generate(client, headers)
    assert response.status_code == 409
    assert "missing or unverified safety metadata" in response.json()["detail"]
    assert str(next(iter(food_ids.values()))) in response.json()["detail"]


@pytest.mark.parametrize(
    ("restriction", "ingredient"),
    [
        ("Peanuts", "peanut flour"),
        ("Tree nuts", "almonds"),
        ("Milk and dairy", "whey"),
        ("Eggs", "eggs"),
        ("Soy", "soybean oil"),
        ("Wheat and gluten", "wheat flour"),
        ("Fish", "salmon"),
        ("Shellfish", "shrimp"),
        ("Sesame", "tahini"),
    ],
)
def test_each_supported_allergy_matches_verified_ingredients(restriction, ingredient):
    metadata = SimpleNamespace(
        IsVerified=True,
        Ingredients=f"rice, {ingredient}",
        Allergens=ingredient,
        CrossContactWarnings="",
        VerificationSource="Test fixture",
        VerifiedAt=datetime.now(),
    )
    assert not is_allergy_safe(metadata, [restriction])


def test_multiple_allergies_cross_contact_and_unknown_metadata_fail_closed():
    safe_for_peanut = SimpleNamespace(
        IsVerified=True,
        Ingredients="rice, vegetables",
        Allergens="",
        CrossContactWarnings="May contain sesame",
        VerificationSource="Test fixture",
        VerifiedAt=datetime.now(),
    )
    assert not is_allergy_safe(safe_for_peanut, ["Peanuts", "Sesame"])
    assert not is_allergy_safe(None, ["Peanuts"])
    assert not is_allergy_safe(
        SimpleNamespace(
            IsVerified=True,
            Ingredients="rice",
            Allergens=None,
            CrossContactWarnings="",
            VerificationSource="Test fixture",
            VerifiedAt=datetime.now(),
        ),
        ["Peanuts"],
    )
    assert is_allergy_safe(None, [""])


def test_missing_vegan_verification_is_not_inferred_from_the_food_name(api):
    client, session_factory = api
    headers = register_and_onboard(client, "Vegan")
    food_ids = add_foods(session_factory, verified=False)
    response = generate(client, headers)
    assert response.status_code == 409
    assert "verified, suitable foods" in response.json()["detail"]
    assert str(next(iter(food_ids.values()))) in response.json()["detail"]


def test_other_preference_requires_a_catalog_match_for_declared_restrictions(api):
    client, session_factory = api
    headers = register_and_onboard(
        client,
        "Other",
        other_dietary_restrictions="avoid uncommon ingredient",
    )
    add_foods(session_factory)
    response = generate(client, headers)
    assert response.status_code == 409
    assert "cannot verify the custom restrictions" in response.json()["detail"]


def test_one_and_seven_day_plans_use_nutrition_and_avoid_adjacent_repetition(api):
    client, session_factory = api
    headers = register_and_onboard(client, "Vegetarian")
    add_foods(session_factory, repeats=2)

    one_day = generate(client, headers, days=1)
    assert one_day.status_code == 200, one_day.text
    assert len(one_day.json()["Meals"]) == 4
    meal = one_day.json()["Meals"][0]
    item = meal["Items"][0]
    quantity = float(item["Quantity"])
    assert meal["Nutrition"]["Calories"] == round(
        float(item["Food"]["Calories"]) * quantity, 2
    )
    assert meal["Nutrition"]["Fiber"] == round(
        float(item["Food"]["Fiber"]) * quantity, 2
    )
    assert len(one_day.json()["DailyNutrition"]) == 1

    seven_day = generate(client, headers, days=7)
    assert seven_day.status_code == 200, seven_day.text
    plan = seven_day.json()
    assert len(plan["Meals"]) == 28
    assert len(plan["DailyNutrition"]) == 7
    meals_by_type = {}
    for meal in plan["Meals"]:
        meals_by_type.setdefault(meal["MealType"], []).append(meal)
    for meals in meals_by_type.values():
        for previous, current in zip(meals, meals[1:]):
            assert previous["Items"][0]["FoodID"] != current["Items"][0]["FoodID"]


def test_insufficient_verified_foods_returns_actionable_catalog_limitation(api):
    client, session_factory = api
    headers = register_and_onboard(client, "Vegan")
    food_ids = add_foods(session_factory, verified=True)
    with session_factory() as db:
        for metadata in db.scalars(select(FoodSafetyMetadata)).all():
            metadata.IsVegan = False
        db.commit()
    response = generate(client, headers)
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "Add reliable ingredient" in detail


def test_profile_restrictions_round_trip_and_apply_only_to_their_owner(api):
    client, session_factory = api
    headers = register_and_onboard(
        client,
        "No preference",
        allergies="Peanuts",
        intolerances="Lactose",
        foods_to_avoid="mushrooms",
        other_dietary_restrictions="no beef",
    )
    profile = client.get("/api/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["profile"]["allergies"] == "Peanuts"
    assert profile.json()["profile"]["intolerances"] == "Lactose"
    assert profile.json()["profile"]["foods_to_avoid"] == "mushrooms"
    assert profile.json()["profile"]["other_dietary_restrictions"] == "no beef"

    other_headers = register_and_onboard(client, "No preference")
    add_foods(session_factory, verified=False)
    assert generate(client, headers).status_code == 409
    other_plan = generate(client, other_headers)
    assert other_plan.status_code == 200, other_plan.text


def test_saving_retry_retrieval_and_food_relationships_are_idempotent(api):
    client, session_factory = api
    headers = register_and_onboard(client)
    food_ids = add_foods(session_factory, verified=False)
    generated = generate(client, headers)
    assert generated.status_code == 200, generated.text

    first = client.post("/api/v1/diet-plans/", headers=headers, json=generated.json())
    assert first.status_code == 201, first.text
    plan_id = first.json()["PlanID"]
    retry = client.post("/api/v1/diet-plans/", headers=headers, json=generated.json())
    assert retry.status_code == 201, retry.text
    assert retry.json()["PlanID"] == plan_id
    assert retry.json()["Meals"][0]["Items"][0]["FoodID"] in food_ids.values()
    assert client.get("/api/v1/diet-plans/", headers=headers).json()[0]["PlanID"] == plan_id
    detail = client.get(f"/api/v1/diet-plans/{plan_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["PlanID"] == plan_id
    with session_factory() as db:
        assert len(db.scalars(select(DietPlan)).all()) == 1


def test_food_catalog_exposes_unknown_safety_status(api):
    client, session_factory = api
    add_foods(session_factory, verified=False)
    food = client.get("/api/v1/foods/").json()[0]
    assert food["SafetyStatus"] == "unknown"
    assert food["IsVerified"] is False
    assert food["Ingredients"] is None
