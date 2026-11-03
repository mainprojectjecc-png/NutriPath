from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Unicode, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.database import Base, utc_now


class User(Base):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column("UserID", Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column("FullName", String(100), nullable=False)
    email: Mapped[str] = mapped_column("Email", String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column("PasswordHash", String(255), nullable=False)
    role: Mapped[str] = mapped_column("Role", String(20), default="User", nullable=False)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, default=utc_now, nullable=False)
    UserID = synonym("id")
    FullName = synonym("full_name")
    Email = synonym("email")
    PasswordHash = synonym("password_hash")
    Role = synonym("role")
    IsActive = synonym("is_active")
    CreatedAt = synonym("created_at")
    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[list["LoginSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "UserProfiles"

    id: Mapped[int] = mapped_column("ProfileID", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        "UserID",
        ForeignKey("Users.UserID", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    age: Mapped[int | None] = mapped_column("Age", Integer)
    height_cm: Mapped[float | None] = mapped_column("HeightCm", Float)
    gender: Mapped[str | None] = mapped_column("Gender", String(40))
    activity_level: Mapped[str | None] = mapped_column("ActivityLevel", String(40))
    dietary_preference: Mapped[str | None] = mapped_column("DietaryPreference", String(60))
    allergies: Mapped[str | None] = mapped_column("Allergies", Text)
    exercise_preferences: Mapped[str | None] = mapped_column("ExercisePreferences", Text)
    daily_routine: Mapped[str | None] = mapped_column("DailyRoutine", Text)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        "OnboardingCompletedAt",
        DateTime,
        default=utc_now,
    )
    current_weight_kg: Mapped[float | None] = mapped_column("CurrentWeightKg", Float)
    target_weight_kg: Mapped[float | None] = mapped_column("TargetWeightKg", Float)
    health_goal: Mapped[str | None] = mapped_column("HealthGoal", String(255))
    created_at: Mapped[datetime | None] = mapped_column("CreatedAt", DateTime, default=utc_now)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    ProfileID = synonym("id")
    UserID = synonym("user_id")
    Age = synonym("age")
    Gender = synonym("gender")
    HeightCm = synonym("height_cm")
    CurrentWeightKg = synonym("current_weight_kg")
    TargetWeightKg = synonym("target_weight_kg")
    HealthGoal = synonym("health_goal")
    CreatedAt = synonym("created_at")
    UpdatedAt = synonym("updated_at")
    user: Mapped[User] = relationship(back_populates="profile")
    goal: Mapped["WeightGoal | None"] = relationship(back_populates="profile", uselist=False, cascade="all, delete-orphan")


class WeightGoal(Base):
    __tablename__ = "weight_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("UserProfiles.ProfileID", ondelete="CASCADE"), unique=True, index=True)
    goal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    starting_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    target_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    profile: Mapped[UserProfile] = relationship(back_populates="goal")


class WeightEntry(Base):
    __tablename__ = "weight_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.UserID", ondelete="CASCADE"), index=True, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    measured_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("UserID", "code", name="uq_achievement_user_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column("UserID", ForeignKey("Users.UserID", ondelete="CASCADE"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column("UserID", ForeignKey("Users.UserID", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user: Mapped[User] = relationship(back_populates="sessions")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column("UserID", ForeignKey("Users.UserID", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column("UserID", ForeignKey("Users.UserID", ondelete="CASCADE"), index=True, nullable=False)
    food_id: Mapped[str] = mapped_column(String(80), nullable=False)
    food_name: Mapped[str] = mapped_column(String(120), nullable=False)
    emoji: Mapped[str] = mapped_column(Unicode(16), default="🥗", nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    serving_label: Mapped[str] = mapped_column(String(80), nullable=False)
    serving_grams: Mapped[float] = mapped_column(Float, nullable=False)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fats: Mapped[float] = mapped_column(Float, nullable=False)
    logged_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class WaterLog(Base):
    __tablename__ = "water_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column("UserID", ForeignKey("Users.UserID", ondelete="CASCADE"), index=True, nullable=False)
    amount_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    logged_on: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class NutritionSettings(Base):
    __tablename__ = "nutrition_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column("UserID", ForeignKey("Users.UserID", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    calorie_goal: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    water_goal: Mapped[int] = mapped_column(Integer, default=2500, nullable=False)
