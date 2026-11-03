import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database import Base, get_db
from app.main import app
from app.models import User, WeightEntry
from app.services.journey import synchronize_baseline


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


def create_journey(client, *, start=75, target=70, goal_type="weight_loss"):
    registration = client.post(
        "/api/auth/register",
        json={
            "full_name": "Journey Tester",
            "email": f"journey-{uuid4().hex}@example.com",
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
            "full_name": "Journey Tester",
            "age": 31,
            "height_cm": 170,
            "gender": None,
            "activity_level": "light",
            "dietary_preference": "No preference",
            "allergies": "",
            "exercise_preferences": "",
            "daily_routine": "",
            "goal": {
                "goal_type": goal_type,
                "starting_weight_kg": start,
                "target_weight_kg": target,
                "duration_weeks": 12,
                "start_date": date.today().isoformat(),
            },
        },
    )
    assert response.status_code == 201, response.text
    return headers


def test_baseline_lookup_compiles_to_sql_server_bit_comparison():
    class CapturingSession:
        statement = None

        def scalar(self, statement):
            self.statement = statement
            return SimpleNamespace(
                weight_kg=75,
                measured_on=date.today(),
                is_baseline=True,
                notes="Starting weight baseline",
            )

    db = CapturingSession()
    synchronize_baseline(
        db,
        SimpleNamespace(id=1),
        SimpleNamespace(starting_weight_kg=75, start_date=date.today()),
    )
    statement = str(db.statement.compile(dialect=mssql.dialect()))
    assert "weight_history.is_baseline = 1" in statement
    assert "weight_history.is_baseline IS 1" not in statement


def save_weight(client, headers, weight, *, measured_on=None, notes=""):
    response = client.post(
        "/api/weight-entries",
        headers=headers,
        json={
            "weight_kg": weight,
            "measured_on": (measured_on or date.today()).isoformat(),
            "notes": notes,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_equal_start_and_current_weight_separates_actual_change_from_target_gap(api):
    client, _ = api
    headers = create_journey(client, start=75, target=70)
    journey = client.get("/api/journey", headers=headers).json()
    assert journey["goal"]["current_weight_kg"] == 75
    assert journey["goal"]["actual_weight_change_kg"] == 0
    assert journey["goal"]["goal_weight_difference_kg"] == 5
    assert journey["goal"]["remaining_weight_kg"] == 5
    assert journey["goal"]["journey_progress_percent"] == 0
    assert len(journey["weight_history"]) == 1
    assert journey["weight_history"][0]["is_baseline"] is True


def test_measurements_update_current_weight_progress_and_persist_after_login(api):
    client, session_factory = api
    headers = create_journey(client, start=75, target=70)
    yesterday = date.today() - timedelta(days=1)
    save_weight(client, headers, 74, measured_on=yesterday, notes="Prior measurement")
    save_weight(client, headers, 73, notes="Latest measurement")

    journey = client.get("/api/journey", headers=headers).json()
    assert journey["goal"]["current_weight_kg"] == 73
    assert journey["goal"]["actual_weight_change_kg"] == -2
    assert journey["goal"]["remaining_weight_kg"] == 3
    assert journey["goal"]["journey_progress_percent"] == 40
    assert len(journey["weight_history"]) == 3

    user = client.get("/api/auth/me", headers=headers).json()
    login = client.post(
        "/api/auth/login",
        json={
            "email": user["email"],
            "password": "secure-password-123",
        },
    )
    refreshed = client.get(
        "/api/journey",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    ).json()
    assert len(refreshed["weight_history"]) == 3
    with session_factory() as db:
        entries = list(db.scalars(select(WeightEntry).order_by(WeightEntry.measured_on)))
        assert len(entries) == 3
        assert sum(entry.is_baseline for entry in entries) == 1


@pytest.mark.parametrize(
    ("goal_type", "start", "target", "measurement", "actual", "remaining"),
    [
        ("weight_loss", 80, 72, 76, -4, 4),
        ("weight_gain", 70, 78, 74, 4, 4),
        ("maintenance", 75, 75, 75, 0, 0),
    ],
)
def test_loss_gain_and_maintenance_progress(api, goal_type, start, target, measurement, actual, remaining):
    client, _ = api
    headers = create_journey(
        client,
        start=start,
        target=target,
        goal_type=goal_type,
    )
    if measurement != start:
        save_weight(client, headers, measurement)
    journey = client.get("/api/journey", headers=headers).json()
    assert journey["goal"]["actual_weight_change_kg"] == actual
    assert journey["goal"]["remaining_weight_kg"] == remaining
    if goal_type == "maintenance":
        assert journey["goal"]["journey_progress_percent"] == 100


def test_goal_edits_recalculate_and_move_only_the_starting_baseline(api):
    client, session_factory = api
    headers = create_journey(client, start=75, target=70)
    earlier = date.today() - timedelta(days=2)
    saved = save_weight(client, headers, 74, measured_on=earlier, notes="Keep this record")
    response = client.put(
        "/api/goals",
        headers=headers,
        json={
            "goal_type": "weight_loss",
            "starting_weight_kg": 76,
            "target_weight_kg": 68,
            "duration_weeks": 16,
            "start_date": date.today().isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["goal"]["actual_weight_change_kg"] == 0
    assert response.json()["goal"]["remaining_weight_kg"] == 8
    journey = client.get("/api/journey", headers=headers).json()
    assert len(journey["weight_history"]) == 2
    assert {item["notes"] for item in journey["weight_history"]} >= {
        "Keep this record",
        "Starting weight baseline",
    }
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email.like("journey-%@example.com")))
        entries = list(db.scalars(select(WeightEntry).where(WeightEntry.user_id == user.id)))
        baseline = next(entry for entry in entries if entry.is_baseline)
        assert baseline.weight_kg == 76
        assert baseline.measured_on == date.today()
        assert any(entry.id == saved["id"] and entry.notes == "Keep this record" for entry in entries)


def test_profile_edits_preserve_measurement_history_and_baseline(api):
    client, _ = api
    headers = create_journey(client)
    save_weight(client, headers, 74, notes="Do not erase")
    before = client.get("/api/journey", headers=headers).json()["weight_history"]
    updated = client.put(
        "/api/profile",
        headers=headers,
        json={
            "full_name": "Updated Journey Tester",
            "age": 32,
            "height_cm": 171,
            "gender": "female",
            "activity_level": "moderate",
            "dietary_preference": "Vegan",
            "allergies": "Sesame",
            "intolerances": "Lactose",
            "foods_to_avoid": "mushrooms",
            "other_dietary_restrictions": "no beef",
            "exercise_preferences": "Walking",
            "daily_routine": "Morning exercise",
        },
    )
    assert updated.status_code == 200, updated.text
    after = client.get("/api/journey", headers=headers).json()["weight_history"]
    assert [(item["id"], item["weight_kg"]) for item in after] == [
        (item["id"], item["weight_kg"]) for item in before
    ]
    assert updated.json()["profile"]["allergies"] == "Sesame"
    assert updated.json()["profile"]["intolerances"] == "Lactose"


def test_omitted_restriction_fields_do_not_clear_existing_profile_values(api):
    client, _ = api
    headers = create_journey(client)
    set_restrictions = client.put(
        "/api/profile",
        headers=headers,
        json={
            "full_name": "Journey Tester",
            "age": 31,
            "height_cm": 170,
            "gender": None,
            "activity_level": "light",
            "dietary_preference": "No preference",
            "allergies": "Peanuts",
            "intolerances": "Lactose",
            "foods_to_avoid": "mushrooms",
            "other_dietary_restrictions": "",
            "exercise_preferences": "",
            "daily_routine": "",
        },
    )
    assert set_restrictions.status_code == 200
    partial = client.put(
        "/api/profile",
        headers=headers,
        json={
            "full_name": "Journey Tester",
            "age": 31,
            "height_cm": 170,
            "gender": None,
            "activity_level": "light",
            "dietary_preference": "No preference",
        },
    )
    assert partial.status_code == 200, partial.text
    assert partial.json()["profile"]["allergies"] == "Peanuts"
    assert partial.json()["profile"]["intolerances"] == "Lactose"
    assert partial.json()["profile"]["foods_to_avoid"] == "mushrooms"
