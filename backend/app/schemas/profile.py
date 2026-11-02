from pydantic import BaseModel, Field
from decimal import Decimal


class ProfileCreate(BaseModel):
    Age: int = Field(..., ge=1, le=120)
    Gender: str = Field(..., max_length=20)
    HeightCm: Decimal = Field(..., gt=0, le=300)
    CurrentWeightKg: Decimal = Field(..., gt=0, le=500)
    TargetWeightKg: Decimal = Field(..., gt=0, le=500)
    HealthGoal: str = Field(..., max_length=100)


class ProfileResponse(ProfileCreate):
    ProfileID: int
    UserID: int

    class Config:
        from_attributes = True