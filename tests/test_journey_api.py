import sys
import unittest
from datetime import date
from unittest.mock import patch
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database import Base, get_db
from app.main import app
from app.models import User


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


if __name__ == "__main__":
    unittest.main()
