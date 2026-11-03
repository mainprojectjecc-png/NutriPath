import os
import sys
import unittest
from datetime import date
from unittest.mock import MagicMock
from unittest.mock import patch
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database import Base, get_db
from app.main import app
from app.models import FoodChangeRequest, FoodItem, NutritionLog, User
from app.security import hash_password, verify_password
from app.services.qa_accounts import QAAccount, provision_qa_accounts


class JourneyApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

        def override_get_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def register(self, email, full_name="Test User"):
        response = self.client.post("/api/auth/register", json={
            "full_name": full_name,
            "email": email,
            "password": "secure-password-123",
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_qa_account_provisioning_is_guarded_by_explicit_confirmation(self):
        from importlib.util import module_from_spec, spec_from_file_location

        script_path = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "provision_qa_accounts.py"
        spec = spec_from_file_location("provision_qa_accounts", script_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.dict(
            "os.environ",
            {
                "NUTRIPATH_ENVIRONMENT": "production",
                "NUTRIPATH_ENABLE_QA_ACCOUNT_PROVISIONING": "I_CONFIRM_QA_ACCOUNT_CREATION",
            },
            clear=True,
        ):
            self.assertEqual(module.main(), 2)

    def test_qa_account_provisioning_rejects_non_sql_server_targets(self):
        from importlib.util import module_from_spec, spec_from_file_location

        script_path = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "provision_qa_accounts.py"
        spec = spec_from_file_location("provision_qa_accounts_target_guard", script_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        db = MagicMock()
        db.get_bind.return_value.dialect.name = "sqlite"
        self.assertIsNone(module._verified_qa_target(db))
        db.execute.assert_not_called()

        db.get_bind.return_value.dialect.name = "mssql"
        db.execute.return_value.one.return_value = ("IMENE", "NutriPathDB")
        self.assertIsNone(module._verified_qa_target(db))

        db.execute.return_value.one.return_value = ("IMENE", "sampledb")
        self.assertEqual(module._verified_qa_target(db), ("IMENE", "sampledb"))

    def test_qa_provisioner_defaults_to_fixed_sql_server_target(self):
        from importlib.util import module_from_spec, spec_from_file_location
        from sqlalchemy.engine import make_url

        script_path = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "provision_qa_accounts.py"
        spec = spec_from_file_location("provision_qa_accounts_url", script_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.dict("os.environ", {}, clear=True):
            module._configure_qa_database_url()
            url = make_url(os.environ["NUTRIPATH_DATABASE_URL"])
            odbc_string = url.query["odbc_connect"]
            self.assertIn("SERVER=lpc:IMENE", odbc_string)
            self.assertIn("DATABASE=sampledb", odbc_string)
            self.assertIn("DRIVER={ODBC Driver 18 for SQL Server}", odbc_string)

        configured_url = "mssql+pyodbc://@localhost/NutriPathDB"
        with patch.dict("os.environ", {"NUTRIPATH_DATABASE_URL": configured_url}, clear=True):
            module._configure_qa_database_url()
            self.assertEqual(os.environ["NUTRIPATH_DATABASE_URL"], configured_url)

    def test_qa_account_provisioning_creates_only_missing_roles(self):
        original_hash = hash_password("existing-user-password")
        with self.session_factory() as db:
            db.add(
                User(
                    full_name="Existing Account",
                    email="qa-user@example.com",
                    password_hash=original_hash,
                    role="Coach",
                    is_active=True,
                )
            )
            db.commit()
            outcomes = provision_qa_accounts(
                db,
                [
                    QAAccount(
                        email="QA-USER@example.com",
                        full_name="QA User",
                        password="qa-user-password-123",
                        role="User",
                    ),
                    QAAccount(
                        email="qa-coach@example.com",
                        full_name="QA Coach",
                        password="qa-coach-password-123",
                        role="Coach",
                    ),
                ],
            )
            self.assertEqual(
                outcomes,
                [
                    "Existing account with a different role left unchanged.",
                    "Created Coach QA account.",
                ],
            )
            existing = db.scalar(select(User).where(User.email == "qa-user@example.com"))
            coach = db.scalar(select(User).where(User.email == "qa-coach@example.com"))
            self.assertEqual(existing.role, "Coach")
            self.assertEqual(existing.password_hash, original_hash)
            self.assertEqual(coach.role, "Coach")
            self.assertNotEqual(coach.password_hash, "qa-coach-password-123")
            self.assertTrue(verify_password("qa-coach-password-123", coach.password_hash))

            repeated = provision_qa_accounts(
                db,
                [
                    QAAccount("qa-user@example.com", "Different User", "different-password-123", "User"),
                    QAAccount("qa-coach@example.com", "Different Coach", "different-password-123", "Coach"),
                ],
            )
            self.assertEqual(
                repeated,
                [
                    "Existing account with a different role left unchanged.",
                    "Existing active Coach account left unchanged.",
                ],
            )
            self.assertEqual(existing.role, "Coach")
            self.assertEqual(existing.password_hash, original_hash)
            self.assertEqual(coach.full_name, "QA Coach")

    def onboard(self, token, full_name="Test User"):
        today = date.today().isoformat()
        return self.client.post(
            "/api/onboarding",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": full_name,
                "age": 31,
                "height_cm": 170,
                "gender": None,
                "activity_level": "light",
                "dietary_preference": "Vegetarian",
                "allergies": "",
                "exercise_preferences": "Walking",
                "daily_routine": "Desk work",
                "goal": {
                    "goal_type": "weight_loss",
                    "starting_weight_kg": 80,
                    "target_weight_kg": 72,
                    "duration_weeks": 12,
                    "start_date": today,
                },
            },
        )

    def test_registration_login_and_password_hashing(self):
        session = self.register("first@example.com")
        self.assertEqual(session["user"]["onboarding_completed"], False)
        with self.session_factory() as db:
            user = db.scalar(select(User).where(User.email == "first@example.com"))
            self.assertNotEqual(user.password_hash, "secure-password-123")
            self.assertTrue(user.password_hash.startswith("pbkdf2_sha256$"))

        login = self.client.post("/api/auth/login", json={
            "email": "first@example.com",
            "password": "secure-password-123",
        })
        self.assertEqual(login.status_code, 200, login.text)
        self.assertEqual(login.json()["user"]["id"], session["user"]["id"])
        bad_login = self.client.post("/api/auth/login", json={
            "email": "first@example.com",
            "password": "incorrect-password",
        })
        self.assertEqual(bad_login.status_code, 401)

    def test_backend_jwt_and_main_auth_share_user_model(self):
        registration = self.client.post("/api/v1/users/register", json={
            "FullName": "Backend User",
            "Email": "backend@example.com",
            "Password": "password-123",
        })
        self.assertEqual(registration.status_code, 201, registration.text)
        user_id = registration.json()["UserID"]

        jwt_login = self.client.post("/api/v1/users/login", data={
            "username": "backend@example.com",
            "password": "password-123",
        })
        self.assertEqual(jwt_login.status_code, 200, jwt_login.text)
        jwt_headers = {"Authorization": f"Bearer {jwt_login.json()['access_token']}"}
        current_user = self.client.get("/api/v1/users/me", headers=jwt_headers)
        self.assertEqual(current_user.status_code, 200, current_user.text)
        self.assertEqual(current_user.json()["user_id"], user_id)
        self.assertEqual(self.client.get("/api/v1/users/me").status_code, 401)

        main_login = self.client.post("/api/auth/login", json={
            "email": "backend@example.com",
            "password": "password-123",
        })
        self.assertEqual(main_login.status_code, 200, main_login.text)
        main_headers = {"Authorization": f"Bearer {main_login.json()['access_token']}"}
        self.assertEqual(self.client.get("/api/auth/me", headers=main_headers).json()["id"], user_id)

    def test_onboarding_weight_history_and_milestones_are_user_scoped(self):
        first = self.register("first@example.com")
        response = self.onboard(first["access_token"])
        self.assertEqual(response.status_code, 201, response.text)
        self.assertTrue(response.json()["user"]["onboarding_completed"])
        self.assertAlmostEqual(response.json()["goal"]["weekly_change_required_kg"], 0.67, places=2)

        headers = {"Authorization": f"Bearer {first['access_token']}"}
        for weight in (79.5, 79):
            entry = self.client.post("/api/weight-entries", headers=headers, json={
                "weight_kg": weight,
                "measured_on": date.today().isoformat(),
                "notes": "Morning measurement",
            })
            self.assertEqual(entry.status_code, 201, entry.text)

        journey = self.client.get("/api/journey", headers=headers)
        self.assertEqual(journey.status_code, 200, journey.text)
        data = journey.json()
        self.assertEqual(len(data["weight_history"]), 2)
        self.assertEqual(data["goal"]["current_weight_kg"], 79)
        self.assertGreater(data["goal"]["journey_progress_percent"], 0)
        self.assertIn("first_milestone", {item["code"] for item in data["achievements"]})

        second = self.register("second@example.com", "Second User")
        other_headers = {"Authorization": f"Bearer {second['access_token']}"}
        self.assertEqual(self.client.get("/api/weight-entries", headers=other_headers).json(), [])
        self.assertIsNone(self.client.get("/api/journey", headers=other_headers).json())

    def test_invalid_goal_and_logout(self):
        session = self.register("first@example.com")
        invalid = self.onboard(session["access_token"])
        self.assertEqual(invalid.status_code, 201)
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        invalid_update = self.client.put("/api/goals", headers=headers, json={
            "goal_type": "weight_loss",
            "starting_weight_kg": 70,
            "target_weight_kg": 75,
            "duration_weeks": 12,
            "start_date": date.today().isoformat(),
        })
        self.assertEqual(invalid_update.status_code, 422)

        logged_out = self.client.post("/api/auth/logout", headers=headers)
        self.assertEqual(logged_out.status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)

    def test_profile_and_goal_updates_persist(self):
        session = self.register("edit@example.com")
        completed = self.onboard(session["access_token"])
        self.assertEqual(completed.status_code, 201, completed.text)
        headers = {"Authorization": f"Bearer {session['access_token']}"}

        updated_profile = self.client.put("/api/profile", headers=headers, json={
            "full_name": "Updated Name",
            "age": 32,
            "height_cm": 171,
            "gender": "female",
            "activity_level": "moderate",
            "dietary_preference": "Vegan",
            "allergies": "Peanuts",
            "exercise_preferences": "Swimming",
            "daily_routine": "Morning workouts",
        })
        self.assertEqual(updated_profile.status_code, 200, updated_profile.text)
        self.assertEqual(updated_profile.json()["user"]["full_name"], "Updated Name")
        self.assertEqual(updated_profile.json()["profile"]["dietary_preference"], "Vegan")

        updated_goal = self.client.put("/api/goals", headers=headers, json={
            "goal_type": "weight_loss",
            "starting_weight_kg": 80,
            "target_weight_kg": 70,
            "duration_weeks": 4,
            "start_date": date.today().isoformat(),
        })
        self.assertEqual(updated_goal.status_code, 200, updated_goal.text)
        self.assertEqual(updated_goal.json()["goal"]["target_weight_kg"], 70)
        self.assertEqual(updated_goal.json()["goal"]["duration_weeks"], 4)
        self.assertTrue(updated_goal.json()["goal"]["unsafe_target"])

    def test_weight_entry_crud_and_ownership(self):
        first = self.register("weight-crud@example.com")
        self.assertEqual(self.onboard(first["access_token"]).status_code, 201)
        first_headers = {"Authorization": f"Bearer {first['access_token']}"}
        second = self.register("weight-other@example.com", "Other User")
        second_headers = {"Authorization": f"Bearer {second['access_token']}"}
        payload = {
            "weight_kg": 78.5,
            "measured_on": date.today().isoformat(),
            "notes": "Initial entry",
        }

        created = self.client.post("/api/weight-entries", headers=first_headers, json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        entry_id = created.json()["id"]
        updated_payload = {**payload, "weight_kg": 77.8, "notes": "Corrected entry"}
        updated = self.client.put(
            f"/api/weight-entries/{entry_id}",
            headers=first_headers,
            json=updated_payload,
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["weight_kg"], 77.8)
        self.assertEqual(updated.json()["notes"], "Corrected entry")
        future_date = date.fromordinal(date.today().toordinal() + 1).isoformat()
        self.assertEqual(
            self.client.put(
                f"/api/weight-entries/{entry_id}",
                headers=first_headers,
                json={**updated_payload, "measured_on": future_date},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.put(
                f"/api/weight-entries/{entry_id}",
                headers=second_headers,
                json=payload,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(f"/api/weight-entries/{entry_id}", headers=second_headers).status_code,
            404,
        )
        history = self.client.get("/api/weight-entries", headers=first_headers)
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(len(history.json()), 1)
        self.assertEqual(history.json()[0]["weight_kg"], 77.8)

        self.assertEqual(self.client.post("/api/auth/logout", headers=first_headers).status_code, 204)
        relogin = self.client.post(
            "/api/auth/login",
            json={"email": "weight-crud@example.com", "password": "secure-password-123"},
        )
        self.assertEqual(relogin.status_code, 200, relogin.text)
        relogin_headers = {"Authorization": f"Bearer {relogin.json()['access_token']}"}
        persisted = self.client.get("/api/weight-entries", headers=relogin_headers)
        self.assertEqual(len(persisted.json()), 1)
        self.assertEqual(persisted.json()[0]["weight_kg"], 77.8)

        deleted = self.client.delete(f"/api/weight-entries/{entry_id}", headers=relogin_headers)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get("/api/weight-entries", headers=relogin_headers).json(), [])

    def test_water_crud_daily_totals_persistence_and_ownership(self):
        first = self.register("water-crud@example.com")
        first_headers = {"Authorization": f"Bearer {first['access_token']}"}
        second = self.register("water-other@example.com", "Other User")
        second_headers = {"Authorization": f"Bearer {second['access_token']}"}
        old_date = "2024-01-02"
        today = date.today().isoformat()

        created = self.client.post(
            "/api/nutrition/water",
            headers=first_headers,
            json={"amount_ml": 300, "date": old_date},
        )
        self.assertEqual(created.status_code, 201, created.text)
        entry_id = created.json()["id"]
        additional = self.client.post(
            "/api/nutrition/water",
            headers=first_headers,
            json={"amount_ml": 500, "date": today},
        )
        self.assertEqual(additional.status_code, 201, additional.text)

        updated = self.client.put(
            f"/api/nutrition/water/{entry_id}",
            headers=first_headers,
            json={"amount_ml": 400, "date": today},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["amount_ml"], 400)
        self.assertEqual(updated.json()["date"], today)
        self.assertEqual(
            self.client.put(
                f"/api/nutrition/water/{entry_id}",
                headers=second_headers,
                json={"amount_ml": 200, "date": today},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(f"/api/nutrition/water/{entry_id}", headers=second_headers).status_code,
            404,
        )

        nutrition = self.client.get("/api/nutrition", headers=first_headers)
        self.assertEqual(nutrition.status_code, 200, nutrition.text)
        self.assertEqual(nutrition.json()["waterByDate"][today], 900)
        self.assertNotIn(old_date, nutrition.json()["waterByDate"])
        self.assertEqual(len(nutrition.json()["waterEntries"]), 2)

        self.assertEqual(self.client.post("/api/auth/logout", headers=first_headers).status_code, 204)
        relogin = self.client.post(
            "/api/auth/login",
            json={"email": "water-crud@example.com", "password": "secure-password-123"},
        )
        self.assertEqual(relogin.status_code, 200, relogin.text)
        relogin_headers = {"Authorization": f"Bearer {relogin.json()['access_token']}"}
        persisted = self.client.get("/api/nutrition", headers=relogin_headers)
        self.assertEqual(persisted.json()["waterByDate"][today], 900)

        deleted = self.client.delete(f"/api/nutrition/water/{entry_id}", headers=relogin_headers)
        self.assertEqual(deleted.status_code, 204)
        remaining = self.client.get("/api/nutrition", headers=relogin_headers)
        self.assertEqual(remaining.json()["waterByDate"][today], 500)
        self.assertEqual([entry["id"] for entry in remaining.json()["waterEntries"]], [additional.json()["id"]])

    def test_diet_plan_generation_persistence_management_and_ownership(self):
        registration = self.register("planner@example.com")
        self.assertEqual(self.onboard(registration["access_token"]).status_code, 201)
        headers = {"Authorization": f"Bearer {registration['access_token']}"}
        other = self.register("planner-other@example.com", "Other User")
        other_headers = {"Authorization": f"Bearer {other['access_token']}"}

        with self.session_factory() as db:
            foods = [
                FoodItem(
                    CatalogID=f"planner-{category.casefold()}",
                    FoodName=f"Planner {category}",
                    Category=category,
                    Calories=calories,
                    Protein=protein,
                    Carbs=carbs,
                    Fat=fat,
                    Fiber=0,
                    ServingSize="1 serving",
                    IsActive=True,
                )
                for category, calories, protein, carbs, fat in (
                    ("Breakfast", 100, 8, 12, 2),
                    ("Lunch", 200, 12, 25, 4),
                    ("Dinner", 250, 20, 10, 8),
                    ("Snacks", 50, 2, 8, 1),
                )
            ]
            db.add_all(foods)
            db.commit()
            food_ids = {food.Category: food.FoodID for food in foods}

        generated = self.client.post(
            "/api/v1/diet-plans/generate",
            headers=headers,
            json={"StartDate": date.today().isoformat(), "Days": 2},
        )
        self.assertEqual(generated.status_code, 200, generated.text)
        generated_plan = generated.json()
        self.assertEqual(generated_plan["GoalType"], "weight_loss")
        self.assertEqual(len(generated_plan["Meals"]), 8)
        for meal in generated_plan["Meals"]:
            self.assertEqual(len(meal["Items"]), 1)
            item = meal["Items"][0]
            self.assertIn(item["FoodID"], food_ids.values())
            self.assertEqual(float(item["Food"]["Calories"]), {
                food_ids["Breakfast"]: 100,
                food_ids["Lunch"]: 200,
                food_ids["Dinner"]: 250,
                food_ids["Snacks"]: 50,
            }[item["FoodID"]])

        created = self.client.post(
            "/api/v1/diet-plans/",
            headers=headers,
            json=generated_plan,
        )
        self.assertEqual(created.status_code, 201, created.text)
        plan_id = created.json()["PlanID"]
        self.assertEqual(len(created.json()["Meals"]), 8)
        self.assertEqual(
            created.json()["Meals"][0]["Items"][0]["Food"]["FoodID"],
            created.json()["Meals"][0]["Items"][0]["FoodID"],
        )

        listed = self.client.get("/api/v1/diet-plans/", headers=headers)
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([plan["PlanID"] for plan in listed.json()], [plan_id])
        updated = self.client.put(
            f"/api/v1/diet-plans/{plan_id}",
            headers=headers,
            json={"PlanName": "Saved vegetarian plan", "Status": "Paused"},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["PlanName"], "Saved vegetarian plan")
        self.assertEqual(updated.json()["Status"], "Paused")
        self.assertEqual(
            self.client.get(f"/api/v1/diet-plans/{plan_id}", headers=other_headers).status_code,
            404,
        )
        self.assertEqual(
            self.client.put(
                f"/api/v1/diet-plans/{plan_id}",
                headers=other_headers,
                json={"Status": "Completed"},
            ).status_code,
            404,
        )

    def test_diet_plan_generation_refuses_unsupported_allergy_safety(self):
        registration = self.register("allergy-plan@example.com")
        headers = {"Authorization": f"Bearer {registration['access_token']}"}
        self.assertEqual(self.onboard(registration["access_token"]).status_code, 201)
        updated = self.client.put("/api/profile", headers=headers, json={
            "full_name": "Test User",
            "age": 31,
            "height_cm": 170,
            "gender": None,
            "activity_level": "light",
            "dietary_preference": "Vegetarian",
            "allergies": "Peanuts",
            "exercise_preferences": "",
            "daily_routine": "",
        })
        self.assertEqual(updated.status_code, 200, updated.text)
        response = self.client.post(
            "/api/v1/diet-plans/generate",
            headers=headers,
            json={"StartDate": date.today().isoformat(), "Days": 1},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("allergen data", response.json()["detail"])

    def test_password_reset_revokes_existing_sessions(self):
        session = self.register("reset@example.com")
        with patch.dict("os.environ", {"NUTRIPATH_SMTP_HOST": "smtp.example.test"}):
            with patch("app.routers.auth._send_reset_email") as send_email:
                requested = self.client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})
                self.assertEqual(requested.status_code, 202, requested.text)
                self.assertEqual(send_email.call_count, 1)
                token = send_email.call_args.args[1]

                reset = self.client.post("/api/auth/reset-password", json={
                    "token": token,
                    "new_password": "a-new-secure-password",
                })
                self.assertEqual(reset.status_code, 200, reset.text)
                self.assertEqual(self.client.get("/api/auth/me", headers={
                    "Authorization": f"Bearer {session['access_token']}",
                }).status_code, 401)

        login = self.client.post("/api/auth/login", json={
            "email": "reset@example.com",
            "password": "a-new-secure-password",
        })
        self.assertEqual(login.status_code, 200, login.text)

    def test_nutrition_logs_and_preferences_are_user_scoped(self):
        first = self.register("nutrition@example.com")
        first_headers = {"Authorization": f"Bearer {first['access_token']}"}
        food = {
            "food_id": "idli",
            "food_name": "Idli",
            "emoji": "🍘",
            "meal_type": "Breakfast",
            "quantity": 2,
            "serving_label": "1 piece",
            "serving_grams": 40,
            "calories": 116,
            "protein": 4,
            "carbs": 24,
            "fats": 0.4,
            "date": date.today().isoformat(),
        }
        added = self.client.post("/api/nutrition/meals", headers=first_headers, json=food)
        self.assertEqual(added.status_code, 201, added.text)
        self.assertEqual(added.json()["foodName"], "Idli")

        water = self.client.post("/api/nutrition/water", headers=first_headers, json={
            "amount_ml": 250,
            "date": date.today().isoformat(),
        })
        self.assertEqual(water.status_code, 201, water.text)
        self.client.put("/api/nutrition/settings", headers=first_headers, json={
            "calorie_goal": 1800,
            "water_goal": 2200,
        })
        nutrition = self.client.get("/api/nutrition", headers=first_headers).json()
        self.assertEqual(len(nutrition["meals"]), 1)
        self.assertEqual(nutrition["waterByDate"][date.today().isoformat()], 250)
        self.assertEqual(nutrition["calorieGoal"], 1800)

        second = self.register("other-nutrition@example.com", "Other User")
        second_headers = {"Authorization": f"Bearer {second['access_token']}"}
        other_nutrition = self.client.get("/api/nutrition", headers=second_headers).json()
        self.assertEqual(other_nutrition["meals"], [])
        self.assertEqual(other_nutrition["waterByDate"], {})
        self.assertEqual(other_nutrition["calorieGoal"], 2000)
        self.assertEqual(self.client.delete(f"/api/nutrition/meals/{added.json()['id']}", headers=second_headers).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/nutrition/meals/{added.json()['id']}", headers=first_headers).status_code, 204)

    def test_nutrition_log_with_food_change_request_cannot_be_deleted(self):
        session = self.register("nutrition-request@example.com")
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        added = self.client.post(
            "/api/nutrition/meals",
            headers=headers,
            json={
                "food_id": "idli",
                "food_name": "Idli",
                "emoji": "🍘",
                "meal_type": "Breakfast",
                "quantity": 1,
                "serving_label": "1 piece",
                "serving_grams": 40,
                "calories": 58,
                "protein": 2,
                "carbs": 12,
                "fats": 0.2,
                "date": date.today().isoformat(),
            },
        )
        self.assertEqual(added.status_code, 201, added.text)
        request = self.client.post(
            "/api/v1/food-change-requests/",
            headers=headers,
            json={
                "NutritionLogID": added.json()["id"],
                "Reason": "Food preference",
            },
        )
        self.assertEqual(request.status_code, 201, request.text)

        rejected_delete = self.client.delete(
            f"/api/nutrition/meals/{added.json()['id']}",
            headers=headers,
        )
        self.assertEqual(rejected_delete.status_code, 409)
        self.assertIn("associated food-change request", rejected_delete.json()["detail"])

        with self.session_factory() as db:
            log = db.get(NutritionLog, added.json()["id"])
            self.assertIsNotNone(log)
            saved_request = db.get(FoodChangeRequest, request.json()["RequestID"])
            self.assertIsNotNone(saved_request)
            self.assertEqual(saved_request.NutritionLogID, log.id)

        other = self.register("another-nutrition-request@example.com")
        other_headers = {"Authorization": f"Bearer {other['access_token']}"}
        self.assertEqual(
            self.client.delete(
                f"/api/nutrition/meals/{added.json()['id']}",
                headers=other_headers,
            ).status_code,
            404,
        )

    def test_inactive_accounts_cannot_use_existing_sessions(self):
        session = self.register("inactive@example.com")
        legacy_registration = self.client.post("/api/v1/users/register", json={
            "FullName": "Inactive Legacy User",
            "Email": "inactive-legacy@example.com",
            "Password": "password-123",
        })
        self.assertEqual(legacy_registration.status_code, 201, legacy_registration.text)
        legacy_login = self.client.post("/api/v1/users/login", data={
            "username": "inactive-legacy@example.com",
            "password": "password-123",
        })
        self.assertEqual(legacy_login.status_code, 200, legacy_login.text)
        with self.session_factory() as db:
            user = db.get(User, session["user"]["id"])
            user.is_active = False
            legacy_user = db.get(User, legacy_registration.json()["UserID"])
            legacy_user.is_active = False
            db.commit()

        response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {session['access_token']}"},
        )
        self.assertEqual(response.status_code, 401)
        inactive_login = self.client.post("/api/auth/login", json={
            "email": "inactive@example.com",
            "password": "secure-password-123",
        })
        self.assertEqual(inactive_login.status_code, 403)
        legacy_response = self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {legacy_login.json()['access_token']}"},
        )
        self.assertEqual(legacy_response.status_code, 401)

    def test_food_replacement_request_coach_suggestion_and_resolution(self):
        member = self.register("member@example.com")
        coach = self.register("coach@example.com", "Coach User")
        member_headers = {"Authorization": f"Bearer {member['access_token']}"}
        coach_headers = {"Authorization": f"Bearer {coach['access_token']}"}
        with self.session_factory() as db:
            coach_user = db.get(User, coach["user"]["id"])
            coach_user.role = "Coach"
            original_food = FoodItem(
                CatalogID="idli",
                FoodName="Idli",
                Category="Breakfast",
                Calories=58,
                Protein=2,
                Carbs=12,
                Fat=0.2,
                Fiber=1,
                ServingSize="1 piece",
                IsActive=True,
            )
            replacement_food = FoodItem(
                CatalogID="poha",
                FoodName="Poha",
                Category="Breakfast",
                Calories=250,
                Protein=5,
                Carbs=42,
                Fat=7,
                Fiber=2,
                ServingSize="1 bowl",
                IsActive=True,
            )
            inactive_food = FoodItem(
                CatalogID="inactive-food",
                FoodName="Inactive food",
                Category="Breakfast",
                Calories=100,
                Protein=2,
                Carbs=10,
                Fat=3,
                Fiber=1,
                ServingSize="1 serving",
                IsActive=False,
            )
            uncatalogued_food = FoodItem(
                CatalogID=None,
                FoodName="Uncatalogued active food",
                Category="Breakfast",
                Calories=100,
                Protein=2,
                Carbs=10,
                Fat=3,
                Fiber=1,
                ServingSize="1 serving",
                IsActive=True,
            )
            db.add_all([original_food, replacement_food, inactive_food, uncatalogued_food])
            db.flush()
            nutrition_entry = NutritionLog(
                user_id=member["user"]["id"],
                food_id="idli",
                food_name="Idli",
                emoji="🍘",
                meal_type="Breakfast",
                quantity=2,
                serving_label="1 piece",
                serving_grams=40,
                calories=116,
                protein=4,
                carbs=24,
                fats=0.4,
                logged_on=date.today(),
            )
            db.add(nutrition_entry)
            db.commit()
            nutrition_entry_id = nutrition_entry.id
            replacement_food_id = replacement_food.FoodID
            inactive_food_id = inactive_food.FoodID
            uncatalogued_food_id = uncatalogued_food.FoodID

        food_catalog = self.client.get("/api/v1/foods/")
        self.assertEqual(food_catalog.status_code, 200, food_catalog.text)
        self.assertEqual(food_catalog.json()[0]["CatalogID"], "idli")

        created = self.client.post(
            "/api/v1/food-change-requests/",
            headers=member_headers,
            json={"NutritionLogID": nutrition_entry_id, "Reason": "Food preference"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        request_id = created.json()["RequestID"]
        duplicate = self.client.post(
            "/api/v1/food-change-requests/",
            headers=member_headers,
            json={"NutritionLogID": nutrition_entry_id, "Reason": "Food preference"},
        )
        self.assertEqual(duplicate.status_code, 409)

        other_member = self.register("other-member@example.com")
        other_headers = {"Authorization": f"Bearer {other_member['access_token']}"}
        self.assertEqual(
            self.client.get(
                f"/api/v1/food-change-requests/{request_id}",
                headers=other_headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/food-change-requests/{request_id}/accept",
                headers=other_headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/coach/requests",
                headers=member_headers,
            ).status_code,
            403,
        )
        invalid_suggestion = self.client.post(
            f"/api/v1/coach/requests/{request_id}/suggestion",
            headers=coach_headers,
            json={"SuggestedFoodID": inactive_food_id},
        )
        self.assertEqual(invalid_suggestion.status_code, 404)

        pending = self.client.get(
            "/api/v1/coach/requests",
            headers=coach_headers,
        )
        self.assertEqual(pending.status_code, 200, pending.text)
        self.assertEqual(pending.json()[0]["Status"], "Pending")
        suggestion = self.client.post(
            f"/api/v1/coach/requests/{request_id}/suggestion",
            headers=coach_headers,
            json={"SuggestedFoodID": replacement_food_id, "Message": "Try this instead."},
        )
        self.assertEqual(suggestion.status_code, 201, suggestion.text)
        self.assertEqual(suggestion.json()["Status"], "Reviewed")
        self.assertNotIn("Email", suggestion.json()["User"])

        accepted = self.client.post(
            f"/api/v1/food-change-requests/{request_id}/accept",
            headers=member_headers,
        )
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()["Status"], "Accepted")
        self.assertEqual(
            accepted.json()["NutritionLog"]["food_name"],
            "Poha",
        )
        self.assertEqual(accepted.json()["NutritionLog"]["food_id"], "poha")

        rejected_request = self.client.post(
            "/api/v1/food-change-requests/",
            headers=member_headers,
            json={"NutritionLogID": nutrition_entry_id, "Reason": "Another option"},
        )
        self.assertEqual(rejected_request.status_code, 201, rejected_request.text)
        rejected_request_id = rejected_request.json()["RequestID"]
        rejected_suggestion = self.client.post(
            f"/api/v1/coach/requests/{rejected_request_id}/suggestion",
            headers=coach_headers,
            json={"SuggestedFoodID": replacement_food_id},
        )
        self.assertEqual(rejected_suggestion.status_code, 201, rejected_suggestion.text)
        rejected = self.client.post(
            f"/api/v1/food-change-requests/{rejected_request_id}/reject",
            headers=member_headers,
        )
        self.assertEqual(rejected.status_code, 200, rejected.text)
        self.assertEqual(rejected.json()["Status"], "Rejected")
        self.assertEqual(rejected.json()["Suggestion"]["Status"], "Rejected")

        uncatalogued_request = self.client.post(
            "/api/v1/food-change-requests/",
            headers=member_headers,
            json={"NutritionLogID": nutrition_entry_id, "Reason": "Test unsupported catalog mapping"},
        )
        self.assertEqual(uncatalogued_request.status_code, 201, uncatalogued_request.text)
        uncatalogued_request_id = uncatalogued_request.json()["RequestID"]
        uncatalogued_suggestion = self.client.post(
            f"/api/v1/coach/requests/{uncatalogued_request_id}/suggestion",
            headers=coach_headers,
            json={"SuggestedFoodID": uncatalogued_food_id},
        )
        self.assertEqual(uncatalogued_suggestion.status_code, 201, uncatalogued_suggestion.text)
        blocked_acceptance = self.client.post(
            f"/api/v1/food-change-requests/{uncatalogued_request_id}/accept",
            headers=member_headers,
        )
        self.assertEqual(blocked_acceptance.status_code, 409, blocked_acceptance.text)
        self.assertIn("no catalog identifier", blocked_acceptance.json()["detail"])
        preserved_request = self.client.get(
            f"/api/v1/food-change-requests/{uncatalogued_request_id}",
            headers=member_headers,
        )
        self.assertEqual(preserved_request.json()["Status"], "Reviewed")
        self.assertEqual(preserved_request.json()["Suggestion"]["Status"], "Pending")
        preserved_nutrition = self.client.get(
            "/api/nutrition",
            headers=member_headers,
        )
        retained_meal = next(
            meal for meal in preserved_nutrition.json()["meals"]
            if meal["id"] == nutrition_entry_id
        )
        self.assertEqual(retained_meal["foodId"], "poha")

        coach_queue = self.client.get(
            "/api/v1/coach/requests",
            headers=coach_headers,
        )
        self.assertEqual(coach_queue.status_code, 200, coach_queue.text)
        statuses = {request["RequestID"]: request["Status"] for request in coach_queue.json()}
        self.assertEqual(statuses[request_id], "Accepted")
        self.assertEqual(statuses[rejected_request_id], "Rejected")

    def test_meal_crud_and_user_isolation(self):
        registration = self.client.post("/api/v1/users/register", json={
            "FullName": "Meal Owner",
            "Email": "meal-owner@example.com",
            "Password": "password-123",
        })
        self.assertEqual(registration.status_code, 201, registration.text)
        login = self.client.post("/api/v1/users/login", data={
            "username": "meal-owner@example.com",
            "password": "password-123",
        })
        self.assertEqual(login.status_code, 200, login.text)
        owner_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        other_registration = self.client.post("/api/v1/users/register", json={
            "FullName": "Another User",
            "Email": "another-meal-user@example.com",
            "Password": "password-123",
        })
        self.assertEqual(other_registration.status_code, 201, other_registration.text)
        other_login = self.client.post("/api/v1/users/login", data={
            "username": "another-meal-user@example.com",
            "password": "password-123",
        })
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

        with self.session_factory() as db:
            food = FoodItem(
                CatalogID="meal-crud-food",
                FoodName="Meal CRUD Food",
                Category="Breakfast",
                Calories=100,
                Protein=5,
                Carbs=10,
                Fat=2,
                Fiber=1,
                ServingSize="1 serving",
                IsActive=True,
            )
            db.add(food)
            db.commit()
            food_id = food.FoodID

        today = date.today().isoformat()
        created_meal = self.client.post(
            "/api/v1/meals/",
            headers=owner_headers,
            json={"MealDate": today, "MealType": "Breakfast"},
        )
        self.assertEqual(created_meal.status_code, 201, created_meal.text)
        meal_id = created_meal.json()["MealID"]
        added_item = self.client.post(
            f"/api/v1/meals/{meal_id}/items",
            headers=owner_headers,
            json={"FoodID": food_id, "Quantity": 1, "ServingUnit": "serving"},
        )
        self.assertEqual(added_item.status_code, 201, added_item.text)
        item_id = added_item.json()["MealItemID"]
        history = self.client.get(
            f"/api/v1/meals/{today}",
            headers=owner_headers,
        )
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(history.json()[0]["Items"][0]["Food"]["FoodName"], "Meal CRUD Food")
        self.assertEqual(
            self.client.delete(f"/api/v1/meals/{meal_id}", headers=other_headers).status_code,
            404,
        )
        updated_item = self.client.put(
            f"/api/v1/meals/{meal_id}/items/{item_id}",
            headers=owner_headers,
            json={"Quantity": 2},
        )
        self.assertEqual(updated_item.status_code, 200, updated_item.text)
        self.assertEqual(float(updated_item.json()["Quantity"]), 2)
        deleted_item = self.client.delete(
            f"/api/v1/meals/{meal_id}/items/{item_id}",
            headers=owner_headers,
        )
        self.assertEqual(deleted_item.status_code, 204)
        deleted_meal = self.client.delete(
            f"/api/v1/meals/{meal_id}",
            headers=owner_headers,
        )
        self.assertEqual(deleted_meal.status_code, 204)


if __name__ == "__main__":
    unittest.main()
