from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.auth import verify_access_token

router = APIRouter(
    prefix="/api/v1/profiles",
    tags=["Profiles"]
)


@router.post("/", response_model=ProfileResponse)
def create_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token)
):
    user_id = current_user["user_id"]

    existing_profile = db.query(UserProfile).filter(
        UserProfile.UserID == user_id
    ).first()

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists"
        )

    new_profile = UserProfile(
        UserID=user_id,
        Age=profile_data.Age,
        Gender=profile_data.Gender,
        HeightCm=profile_data.HeightCm,
        CurrentWeightKg=profile_data.CurrentWeightKg,
        TargetWeightKg=profile_data.TargetWeightKg,
        HealthGoal=profile_data.HealthGoal
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token)
):
    user_id = current_user["user_id"]

    profile = db.query(UserProfile).filter(
        UserProfile.UserID == user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    return profile

@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access_token)
):
    user_id = current_user["user_id"]

    profile = db.query(UserProfile).filter(
        UserProfile.UserID == user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    profile.Age = profile_data.Age
    profile.Gender = profile_data.Gender
    profile.HeightCm = profile_data.HeightCm
    profile.CurrentWeightKg = profile_data.CurrentWeightKg
    profile.TargetWeightKg = profile_data.TargetWeightKg
    profile.HealthGoal = profile_data.HealthGoal

    db.commit()
    db.refresh(profile)

    return profile