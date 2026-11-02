from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RegistrationInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("full_name")
    @classmethod
    def trim_full_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Full name must contain at least two characters.")
        return value


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailInput(BaseModel):
    email: EmailStr


class PasswordResetInput(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=10, max_length=128)


class WeightGoalInput(BaseModel):
    goal_type: Literal["weight_loss", "maintenance", "weight_gain"]
    starting_weight_kg: float = Field(gt=20, le=500)
    target_weight_kg: float = Field(gt=20, le=500)
    duration_weeks: int = Field(ge=1, le=260)
    start_date: date

    @model_validator(mode="after")
    def goal_matches_direction(self):
        if self.goal_type == "weight_loss" and self.target_weight_kg >= self.starting_weight_kg:
            raise ValueError("A weight-loss target must be below your starting weight.")
        if self.goal_type == "weight_gain" and self.target_weight_kg <= self.starting_weight_kg:
            raise ValueError("A weight-gain target must be above your starting weight.")
        if self.goal_type == "maintenance" and abs(self.target_weight_kg - self.starting_weight_kg) > 2:
            raise ValueError("A maintenance target must be within 2 kg of your starting weight.")
        if self.start_date > date.today():
            raise ValueError("Your journey start date cannot be in the future.")
        return self


class ProfileInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=13, le=120)
    height_cm: float = Field(ge=100, le=250)
    gender: str | None = Field(default=None, max_length=40)
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]
    dietary_preference: str = Field(min_length=2, max_length=60)
    allergies: str = Field(default="", max_length=1000)
    exercise_preferences: str = Field(default="", max_length=1000)
    daily_routine: str = Field(default="", max_length=1000)
    goal: WeightGoalInput

    @field_validator("full_name")
    @classmethod
    def trim_full_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Full name must contain at least two characters.")
        return value


class ProfileUpdateInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=13, le=120)
    height_cm: float = Field(ge=100, le=250)
    gender: str | None = Field(default=None, max_length=40)
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]
    dietary_preference: str = Field(min_length=2, max_length=60)
    allergies: str = Field(default="", max_length=1000)
    exercise_preferences: str = Field(default="", max_length=1000)
    daily_routine: str = Field(default="", max_length=1000)

    @field_validator("full_name")
    @classmethod
    def trim_full_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Full name must contain at least two characters.")
        return value


class WeightEntryInput(BaseModel):
    weight_kg: float = Field(gt=20, le=500)
    measured_on: date
    notes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def date_not_in_future(self):
        if self.measured_on > date.today():
            raise ValueError("A weight measurement date cannot be in the future.")
        return self


class NutritionEntryInput(BaseModel):
    food_id: str = Field(min_length=1, max_length=80)
    food_name: str = Field(min_length=1, max_length=120)
    emoji: str = Field(default="🥗", max_length=16)
    meal_type: Literal["Breakfast", "Lunch", "Snacks", "Dinner"]
    quantity: float = Field(gt=0, le=50)
    serving_label: str = Field(min_length=1, max_length=80)
    serving_grams: float = Field(gt=0, le=5000)
    calories: float = Field(ge=0, le=10000)
    protein: float = Field(ge=0, le=1000)
    carbs: float = Field(ge=0, le=2000)
    fats: float = Field(ge=0, le=1000)
    date: date

    @model_validator(mode="after")
    def date_not_in_future(self):
        if self.date > date.today():
            raise ValueError("A meal date cannot be in the future.")
        return self


class WaterEntryInput(BaseModel):
    amount_ml: int = Field(ge=1, le=3000)
    date: date

    @model_validator(mode="after")
    def date_not_in_future(self):
        if self.date > date.today():
            raise ValueError("A water log date cannot be in the future.")
        return self


class NutritionSettingsInput(BaseModel):
    calorie_goal: int = Field(ge=500, le=10000)
    water_goal: int = Field(ge=250, le=10000)


class UserView(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    onboarding_completed: bool

    model_config = ConfigDict(from_attributes=True)


class WeightEntryView(BaseModel):
    id: int
    weight_kg: float
    measured_on: date
    notes: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AchievementView(BaseModel):
    code: str
    title: str
    description: str
    achieved_at: datetime

    model_config = ConfigDict(from_attributes=True)
