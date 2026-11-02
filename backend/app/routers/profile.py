from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Achievement, User, UserProfile, WeightEntry, WeightGoal
from app.schemas.schemas import ProfileInput, ProfileUpdateInput, WeightEntryInput, WeightGoalInput
from app.security import current_user
from app.services.journey import current_weight_for, ensure_achievements, goal_calculations, profile_payload

router = APIRouter(prefix="/api", tags=["journey"])


def _upsert_goal(db: Session, profile: UserProfile, payload: WeightGoalInput) -> WeightGoal:
    goal = profile.goal
    values = payload.model_dump()
    if goal:
        for key, value in values.items():
            setattr(goal, key, value)
    else:
        goal = WeightGoal(profile=profile, **values)
        db.add(goal)
    profile.goal = goal
    return goal


@router.get("/profile")
def get_profile(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return profile_payload(db, user)


@router.post("/onboarding", status_code=status.HTTP_201_CREATED)
def complete_onboarding(payload: ProfileInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.profile and user.profile.goal:
        raise HTTPException(status_code=409, detail="Onboarding has already been completed. Update your profile instead.")
    user.full_name = payload.full_name.strip()
    values = payload.model_dump(exclude={"goal", "full_name"})
    profile = user.profile or UserProfile(user=user, **values)
    if user.profile:
        for key, value in values.items():
            setattr(profile, key, value)
    db.add(profile)
    db.flush()
    goal = _upsert_goal(db, profile, payload.goal)
    db.commit()
    db.refresh(profile)
    ensure_achievements(db, user, profile, goal, goal.starting_weight_kg)
    return profile_payload(db, user)


@router.put("/profile")
def update_profile(payload: ProfileUpdateInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not user.profile or not user.profile.goal:
        raise HTTPException(status_code=409, detail="Complete onboarding before editing your profile.")
    user.full_name = payload.full_name.strip()
    for key, value in payload.model_dump(exclude={"full_name"}).items():
        setattr(user.profile, key, value)
    db.commit()
    return profile_payload(db, user)


@router.put("/goals")
def update_goal(payload: WeightGoalInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not user.profile or not user.profile.goal:
        raise HTTPException(status_code=409, detail="Complete onboarding before updating your goal.")
    goal = _upsert_goal(db, user.profile, payload)
    db.commit()
    ensure_achievements(db, user, user.profile, goal, current_weight_for(db, user, goal))
    return profile_payload(db, user)


@router.post("/weight-entries", status_code=status.HTTP_201_CREATED)
def add_weight_entry(payload: WeightEntryInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not user.profile or not user.profile.goal:
        raise HTTPException(status_code=409, detail="Complete onboarding before tracking your weight.")
    entry = WeightEntry(user_id=user.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    ensure_achievements(db, user, user.profile, user.profile.goal, current_weight_for(db, user, user.profile.goal))
    return entry


@router.get("/weight-entries")
def get_weight_entries(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return list(db.scalars(select(WeightEntry).where(WeightEntry.user_id == user.id).order_by(WeightEntry.measured_on, WeightEntry.created_at, WeightEntry.id)).all())


@router.get("/journey")
def get_journey(db: Session = Depends(get_db), user: User = Depends(current_user)):
    payload = profile_payload(db, user)
    if not payload:
        return None
    goal = user.profile.goal
    current = current_weight_for(db, user, goal)
    history = list(db.scalars(select(WeightEntry).where(WeightEntry.user_id == user.id).order_by(WeightEntry.measured_on, WeightEntry.created_at, WeightEntry.id)).all())
    achievements = ensure_achievements(db, user, user.profile, goal, current)
    return {
        **payload,
        "weight_history": [
            {"id": entry.id, "weight_kg": entry.weight_kg, "measured_on": entry.measured_on, "notes": entry.notes, "created_at": entry.created_at}
            for entry in history
        ],
        "achievements": [
            {"code": item.code, "title": item.title, "description": item.description, "achieved_at": item.achieved_at}
            for item in achievements
        ],
    }


@router.get("/achievements")
def get_achievements(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return list(db.scalars(select(Achievement).where(Achievement.user_id == user.id).order_by(Achievement.achieved_at)).all())
