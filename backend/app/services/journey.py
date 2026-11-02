from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Achievement, User, UserProfile, WeightEntry, WeightGoal
from app.database import utc_now

ACHIEVEMENT_DEFINITIONS = {
    "journey_started": ("Journey started", "Your personalized journey is underway."),
    "first_week": ("First week complete", "You have been on your journey for a week."),
    "first_milestone": ("First milestone", "You have made your first measurable progress."),
    "progress_25": ("25% progress", "You have completed a quarter of your goal."),
    "progress_50": ("Halfway there", "You have reached 50% of your goal."),
    "progress_75": ("75% progress", "Your goal is coming into view."),
    "goal_reached": ("Goal reached", "You reached your recorded target weight."),
}


def goal_calculations(goal: WeightGoal, profile: UserProfile, current_weight: float) -> dict:
    difference = abs(goal.target_weight_kg - goal.starting_weight_kg)
    weekly_change = difference / goal.duration_weeks
    target_date = goal.start_date + timedelta(weeks=goal.duration_weeks)
    direction = 1 if goal.target_weight_kg < goal.starting_weight_kg else -1 if goal.target_weight_kg > goal.starting_weight_kg else 0
    achieved = max(0, (goal.starting_weight_kg - current_weight) * direction)
    progress = 100 if difference == 0 else min(100, max(0, achieved / difference * 100))
    weekly_percent = weekly_change / goal.starting_weight_kg * 100
    height_m = profile.height_cm / 100
    current_bmi = current_weight / (height_m * height_m)
    target_bmi = goal.target_weight_kg / (height_m * height_m)
    minor = profile.age < 18
    unsafe = goal.goal_type == "weight_loss" and (
        minor or weekly_change > 0.9 or weekly_percent > 1 or (not minor and target_bmi < 18.5)
    )
    return {
        "goal_type": goal.goal_type,
        "starting_weight_kg": goal.starting_weight_kg,
        "target_weight_kg": goal.target_weight_kg,
        "current_weight_kg": current_weight,
        "total_weight_difference_kg": round(difference, 1),
        "remaining_weight_kg": round(abs(goal.target_weight_kg - current_weight), 1),
        "weekly_change_required_kg": round(weekly_change, 2),
        "duration_weeks": goal.duration_weeks,
        "start_date": goal.start_date,
        "target_date": target_date,
        "journey_progress_percent": round(progress, 1),
        "current_bmi": None if minor else round(current_bmi, 1),
        "target_bmi": None if minor else round(target_bmi, 1),
        "unsafe_target": unsafe,
        "safety_message": (
            "Weight-loss goals for people under 18 should be planned with a qualified health professional."
            if minor and goal.goal_type == "weight_loss"
            else "This target may require a faster rate of change or a lower target weight than is generally considered safe. Consider discussing your plan with a qualified health professional."
            if unsafe else None
        ),
        "status": "goal_reached" if progress >= 100 else "in_progress" if date.today() <= target_date else "target_date_passed",
    }


def current_weight_for(db: Session, user: User, goal: WeightGoal) -> float:
    latest = db.scalar(
        select(WeightEntry)
        .where(WeightEntry.user_id == user.id)
        .order_by(WeightEntry.measured_on.desc(), WeightEntry.created_at.desc(), WeightEntry.id.desc())
        .limit(1)
    )
    return latest.weight_kg if latest else goal.starting_weight_kg


def ensure_achievements(db: Session, user: User, profile: UserProfile, goal: WeightGoal, current_weight: float) -> list[Achievement]:
    progress = goal_calculations(goal, profile, current_weight)["journey_progress_percent"]
    codes = ["journey_started"]
    if date.today() >= goal.start_date + timedelta(days=7):
        codes.append("first_week")
    if progress >= 10:
        codes.append("first_milestone")
    codes.extend(code for threshold, code in ((25, "progress_25"), (50, "progress_50"), (75, "progress_75"), (100, "goal_reached")) if progress >= threshold)

    existing = set(db.scalars(select(Achievement.code).where(Achievement.user_id == user.id)).all())
    for code in codes:
        if code not in existing:
            title, description = ACHIEVEMENT_DEFINITIONS[code]
            db.add(Achievement(user_id=user.id, code=code, title=title, description=description, achieved_at=utc_now()))
    if any(code not in existing for code in codes):
        db.commit()
    return list(db.scalars(select(Achievement).where(Achievement.user_id == user.id).order_by(Achievement.achieved_at)).all())


def profile_payload(db: Session, user: User) -> dict | None:
    profile = user.profile
    goal = profile.goal if profile else None
    if not profile or not goal:
        return None
    current = current_weight_for(db, user, goal)
    return {
        "user": {"id": user.id, "full_name": user.full_name, "email": user.email, "onboarding_completed": True},
        "profile": {
            "age": profile.age,
            "height_cm": profile.height_cm,
            "gender": profile.gender,
            "activity_level": profile.activity_level,
            "dietary_preference": profile.dietary_preference,
            "allergies": profile.allergies,
            "exercise_preferences": profile.exercise_preferences,
            "daily_routine": profile.daily_routine,
        },
        "goal": goal_calculations(goal, profile, current),
    }
